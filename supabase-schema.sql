-- ============================================================================
-- 투로그 TwoLog — Supabase 스키마
-- ----------------------------------------------------------------------------
-- Supabase 대시보드 → SQL Editor 에 이 파일 전체를 붙여 넣고 RUN 하면 끝입니다.
--   · 테이블 5개 : couples, events, notes, photos, settings
--   · RLS       : 커플 구성원(auth.uid())만 자기 커플 데이터를 읽고 씁니다
--   · 함수      : join_couple_by_code(6자리 코드로 연결), leave_couple()
--   · Storage   : 비공개 버킷 'photos' + 커플 폴더만 접근
--   · Realtime  : events/notes/photos/settings/couples 변경 알림
-- ============================================================================

-- 0) 확장
create extension if not exists pgcrypto;

-- 1) 커플 ---------------------------------------------------------------------
create table if not exists public.couples (
  id          uuid primary key default gen_random_uuid(),
  invite_code text not null unique check (invite_code ~ '^[0-9]{6}$'),
  members     uuid[] not null default '{}',           -- [만든 사람, 초대받은 사람]
  me          text not null default '나',              -- 만든 사람 기준 이름
  you         text not null default '상대',
  since       date not null default current_date,
  phrase      text not null default '함께한 지',
  fmt         text not null default 'D' check (fmt in ('D','Y')),
  colors      jsonb not null default '{"me":"#F7C6D4","you":"#BCE0F7"}'::jsonb,
  sched       jsonb not null default '{"me":"#F7C6D4","you":"#BCE0F7","both":"#D6C5F7"}'::jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  constraint couples_max_two check (array_length(members, 1) is null or array_length(members, 1) <= 2)
);

-- 2) 일정 ---------------------------------------------------------------------
create table if not exists public.events (
  id         text primary key,
  couple_id  uuid not null references public.couples(id) on delete cascade,
  title      text not null default '',
  date       date not null,
  time       text not null default '',
  type       text not null default 'date' check (type in ('date','anni','trip','etc')),
  memo       text not null default '',
  who        text not null default 'both' check (who in ('me','you','both')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists events_couple_date_idx on public.events (couple_id, date);

-- 3) 노트 (할일 / 버킷 / 영화·먹방 / 커스텀 리스트) ---------------------------
create table if not exists public.notes (
  id         text primary key,
  couple_id  uuid not null references public.couples(id) on delete cascade,
  kind       text not null check (kind in ('todo','bucket','log','list')),
  payload    jsonb not null default '{}'::jsonb,
  sort       numeric not null default 0,
  deleted    boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists notes_couple_kind_idx on public.notes (couple_id, kind, sort);

-- 4) 사진 ---------------------------------------------------------------------
--    storage_path : Storage 버킷 'photos' 안의 경로  (<couple_id>/<photo_id>.jpg)
create table if not exists public.photos (
  id           text primary key,
  couple_id    uuid not null references public.couples(id) on delete cascade,
  date         date not null default current_date,
  album        text not null default '',
  title        text not null default '',
  place        text not null default '',
  memo         text not null default '',
  art          int,
  cap_bg       text,
  storage_path text,
  sort         numeric not null default 0,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists photos_couple_date_idx on public.photos (couple_id, date desc);

-- 5) 설정 (테마 등 공유 값) ----------------------------------------------------
create table if not exists public.settings (
  couple_id  uuid not null references public.couples(id) on delete cascade,
  key        text not null,
  value      jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (couple_id, key)
);

-- 6) updated_at 자동 갱신 -------------------------------------------------------
create or replace function public.touch_updated()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

do $$
declare t text;
begin
  foreach t in array array['couples','events','notes','photos','settings'] loop
    execute format('drop trigger if exists %I_touch on public.%I', t, t);
    execute format('create trigger %I_touch before update on public.%I for each row execute function public.touch_updated()', t, t);
  end loop;
end $$;

-- 7) 커플 구성원 확인 (RLS 에서 재사용) -----------------------------------------
create or replace function public.is_couple_member(cid uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.couples c
     where c.id = cid and auth.uid() = any (c.members)
  );
$$;

-- 8) 커플 연결 / 해제 -----------------------------------------------------------
create or replace function public.join_couple_by_code(code text)
returns public.couples
language plpgsql
security definer
set search_path = public
as $$
declare
  c   public.couples;
  uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not_authenticated'; end if;

  select * into c from public.couples where invite_code = trim(code) limit 1;
  if c.id is null then raise exception 'code_not_found'; end if;
  if uid = any (c.members) then return c; end if;
  if array_length(c.members, 1) >= 2 then raise exception 'couple_full'; end if;

  update public.couples
     set members = array_append(members, uid),
         updated_at = now()
   where id = c.id
   returning * into c;

  -- 초대받은 사람이 혼자 쓰다 만 '빈 커플'이 있으면 정리 (기록이 있는 커플은 그대로 둡니다)
  delete from public.couples c2
   where c2.id <> c.id
     and c2.members = array[uid]
     and not exists (select 1 from public.events e where e.couple_id = c2.id)
     and not exists (select 1 from public.notes n where n.couple_id = c2.id)
     and not exists (select 1 from public.photos p where p.couple_id = c2.id);

  return c;
end $$;

create or replace function public.leave_couple()
returns void
language plpgsql
security definer
set search_path = public
as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not_authenticated'; end if;
  update public.couples
     set members = array_remove(members, uid), updated_at = now()
   where uid = any (members);
end $$;

revoke all on function public.join_couple_by_code(text) from anon;
revoke all on function public.leave_couple() from anon;
grant execute on function public.join_couple_by_code(text) to authenticated;
grant execute on function public.leave_couple() to authenticated;
grant execute on function public.is_couple_member(uuid) to authenticated;

-- 9) RLS ----------------------------------------------------------------------
alter table public.couples  enable row level security;
alter table public.events   enable row level security;
alter table public.notes    enable row level security;
alter table public.photos   enable row level security;
alter table public.settings enable row level security;

-- couples : 구성원만 읽기 / 만들기 / 고치기 (삭제는 대시보드에서만)
drop policy if exists couples_select on public.couples;
drop policy if exists couples_insert on public.couples;
drop policy if exists couples_update on public.couples;
create policy couples_select on public.couples for select to authenticated
  using (auth.uid() = any (members));
create policy couples_insert on public.couples for insert to authenticated
  with check (auth.uid() = any (members));
create policy couples_update on public.couples for update to authenticated
  using (auth.uid() = any (members))
  with check (auth.uid() = any (members));

-- events / notes / photos / settings : 커플 구성원만
do $$
declare t text;
begin
  foreach t in array array['events','notes','photos'] loop
    execute format('drop policy if exists %I_couple_all on public.%I', t, t);
    execute format($f$create policy %I_couple_all on public.%I for all to authenticated
      using (public.is_couple_member(couple_id))
      with check (public.is_couple_member(couple_id))$f$, t, t);
  end loop;

  drop policy if exists settings_couple_all on public.settings;
  create policy settings_couple_all on public.settings for all to authenticated
    using (public.is_couple_member(couple_id))
    with check (public.is_couple_member(couple_id));
end $$;

-- 10) Storage : 비공개 사진 버킷 -------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('photos', 'photos', false, 10485760, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update
  set public = false,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

-- 경로 규칙: <couple_id>/<photo_id>.jpg  → 그 커플 구성원만 접근
drop policy if exists photos_storage_read on storage.objects;
drop policy if exists photos_storage_write on storage.objects;
drop policy if exists photos_storage_update on storage.objects;
drop policy if exists photos_storage_delete on storage.objects;

create policy photos_storage_read on storage.objects for select to authenticated
  using (bucket_id = 'photos' and public.is_couple_member(((storage.foldername(name))[1])::uuid));

create policy photos_storage_write on storage.objects for insert to authenticated
  with check (bucket_id = 'photos' and public.is_couple_member(((storage.foldername(name))[1])::uuid));

create policy photos_storage_update on storage.objects for update to authenticated
  using (bucket_id = 'photos' and public.is_couple_member(((storage.foldername(name))[1])::uuid));

create policy photos_storage_delete on storage.objects for delete to authenticated
  using (bucket_id = 'photos' and public.is_couple_member(((storage.foldername(name))[1])::uuid));

-- 11) Realtime -----------------------------------------------------------------
--   DELETE 이벤트에도 couple_id 가 실려 오도록 replica identity 를 full 로.
alter table public.events   replica identity full;
alter table public.notes    replica identity full;
alter table public.photos   replica identity full;
alter table public.settings replica identity full;
alter table public.couples  replica identity full;

do $$
declare t text;
begin
  foreach t in array array['events','notes','photos','settings','couples'] loop
    begin
      execute format('alter publication supabase_realtime add table public.%I', t);
    exception
      when duplicate_object then null;
      when undefined_object then null;   -- publication 이 아직 없으면 무시
    end;
  end loop;
end $$;

-- 12) 권한 ---------------------------------------------------------------------
grant usage on schema public to authenticated;
grant select, insert, update, delete on public.couples, public.events, public.notes, public.photos, public.settings to authenticated;

-- 끝. 이제 sync.js 의 CONFIG.supabaseUrl / supabaseAnonKey 를 채우면 remote 모드로 동작합니다.
