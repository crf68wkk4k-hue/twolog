# 투로그 · TwoLog

둘이 함께 쌓는 캘린더 · 노트 · 사진첩. 순수 HTML/CSS/JS 로 만든 설치형 웹앱(PWA)입니다.
빌드 도구도, 프레임워크도 없습니다. 폴더를 웹에 올리면 그대로 앱이 됩니다.

- **지금 바로** — 이 기기에서 혼자 쓰는 **로컬 모드**로도 완전히 동작합니다(인터넷·가입 필요 없음, 기록은 기기에 저장).
- **두 대 동기화** — `sync.js` 의 `CONFIG` 두 칸에 Supabase 주소/키를 넣으면 **실시간 동기화 모드**로 바뀝니다(무료 플랜으로 충분).
- **v25 부터**는 소영·준영의 프로젝트(`qvhupdivtfzhzymovtyy`)가 `CONFIG` 에 들어 있어 **배포 주소는 동기화 모드가 기본**입니다(로그인 화면 → 이메일 계정).
  기기에만 저장하는 예전 방식으로 열어 보려면 주소 뒤에 `?sync=local` 을 붙입니다(테스트도 이 통로를 씁니다).
- **v26 부터**는 폰에만 남아 있던 예전 기록(localStorage + IndexedDB)을 **처음 로그인할 때 한 번 자동으로 새 커플 공간으로 이어 옵니다**.
  이미 옮긴 기기는 다시 옮기지 않고(플래그 `twolog.migrated.<coupleId>`), 원본은 폰에 그대로 남깁니다.
  원격에 이미 기록이 있으면 자동으로는 건드리지 않고 **My 탭 → 「폰에 있던 예전 기록 가져오기」** 로 겹치지 않게 더할 수 있어요.
  같은 버전에서 **프로필 사진도 사람별로 동기화**됩니다(내 사진은 내가, 상대 사진은 상대 폰에서).

---

## 1. 폴더 구조

```
twolog/
├─ index.html              화면 뼈대 (5개 탭 + 시트 + 사진 선택 input)
├─ styles.css               디자인 전체 (화이트/#111 다크, 100% 각진 모서리, Pretendard)
├─ app.js                   화면 그리기 + 모든 상호작용 (5탭, 폼, 사진 업로드/편집)
├─ sync.js                  데이터 계층 — local(localStorage+IndexedDB) / remote(Supabase)
├─ supabase-schema.sql      Supabase 에 그대로 붙여 넣는 스키마 (테이블 5 + RLS + Storage + Realtime)
├─ manifest.json            PWA 매니페스트 (standalone, 테마/배경 #FFFFFF, 아이콘 3종)
├─ sw.js                    서비스 워커 — 앱 껍데기 캐시(오프라인에서도 열림)
├─ icons/
│   ├─ icon-192.png / icon-512.png        앱 아이콘 (흰 바탕 · 먹색/코랄 사각 두 개)
│   ├─ icon-maskable-512.png              안드로이드 마스커블용
│   ├─ apple-touch-icon.png (180)         iOS 홈 화면 아이콘
│   └─ favicon.svg / favicon-32.png
└─ assets/fonts/pretendard-{400,500,600,700}.woff2   Pretendard (자체 호스팅, 오프라인 OK)
```

---

## 2. 지금 바로 열어 보기 (로컬 서버)

```bash
cd twolog
python3 -m http.server 8080
# 브라우저에서 http://localhost:8080
```

- 핸드폰에서 보려면 같은 와이파이에서 `http://<맥/PC의 IP>:8080`.
- **`?demo=1`** 을 붙이면 프로토타입 v4 의 예시 데이터(일정 10개·사진 12장 등)로 화면을 볼 수 있습니다.
  예시 화면에서는 저장이 잠겨 있어 진짜 기록을 건드리지 않습니다.
- 처음 열면 기록이 **비어 있는 상태**로 시작합니다. 이름·만난 날은 **설정 → 커플 정보**에서 바꾸세요.

> 로컬 서버는 확인용입니다. 폰 홈 화면에 설치하고 실제로 쓰려면 아래 3장(배포)으로 넘어가세요.
> (서비스 워커는 `https://` 또는 `localhost` 에서만 동작합니다.)

---

## 3. 배포 — 3분이면 끝

정적 파일만 있으니 어디든 됩니다. 대표적으로 **Vercel**:

1. <https://vercel.com> 로그인 → **Add New → Project**
2. `twolog` 폴더를 드래그해 업로드(또는 GitHub 저장소 연결)
   - Framework Preset: **Other**, Build Command: 비움, Output Directory: **`./`**
3. Deploy → `https://twolog-xxxx.vercel.app` 주소가 나옵니다.

**Netlify**: <https://app.netlify.com/drop> 에 `twolog` 폴더를 통째로 끌어다 놓으면 끝.
**GitHub Pages**: 저장소에 폴더를 올리고 Settings → Pages → Branch `main` / `/root`.

배포 후 확인:
- `https://주소/manifest.json` 이 열리고, `https://주소/icons/icon-192.png` 가 보이면 정상.

---

## 4. 아이폰 홈 화면에 추가 (설치)

Safari 로 배포 주소를 연 뒤:

1. 하단 **공유** 버튼 → **홈 화면에 추가**
2. 이름이 **투로그** 로 들어갑니다 → **添加/추가**
3. 홈 화면 아이콘으로 열면 주소창 없는 전체 화면(standalone)으로 뜹니다.

- 상태바는 흰 배경에 맞춘 `default` 스타일이고, 상단/하단 안전 영역(노치·홈 인디케이터)을 비켜 배치했습니다.
- 한 번 열어 두면 서비스 워커가 앱을 캐시해서 **비행기 모드에서도 열립니다**(기록은 기기에 있으니 그대로 보입니다).
- 새 버전을 올렸을 때는 앱을 완전히 닫(앱 전환기에서 위로 밀기)았다가 다시 열면 갱신됩니다.

---

## 5. 두 대 실시간 동기화 (Supabase 무료 플랜)

### 5-1. 프로젝트 만들기
1. <https://supabase.com> 가입 → **New project** (리전: `Northeast Asia (Seoul)` 추천)
2. Database 비밀번호는 따로 적어 두세요(이 앱에서는 쓰지 않지만 복구용).

### 5-2. 스키마 넣기
1. 왼쪽 **SQL Editor → New query**
2. 이 폴더의 **`supabase-schema.sql` 전체**를 붙여 넣고 **Run**
3. 만들어지는 것
   - 테이블 5개: `couples`(우리 커플 한 줄) · `events`(일정) · `notes`(할일/버킷/영화·먹방/리스트) · `photos`(사진 정보) · `settings`(테마)
   - RLS: **커플 구성원만** 자기 데이터 읽기/쓰기 (`is_couple_member`)
   - 함수: `join_couple_by_code(code)` · `leave_couple()`
   - Storage: **비공개** 버킷 `photos` (경로 `<couple_id>/<photo_id>.jpg`, 구성원만 접근)
   - Realtime 발행 설정(`events`/`notes`/`photos`/`settings`/`couples`)

### 5-3. 로그인 방식
- **Authentication → Providers → Email** 이 켜져 있는지 확인.
- 두 사람이 바로 쓰려면 **Authentication → Sign In / Providers → Email → "Confirm email" 을 끄는 것**이 가장 간단합니다.
  (켜 두면 가입 후 메일의 확인 링크를 먼저 눌러야 로그인됩니다.)

### 5-4. 주소와 키 넣기
**v25 에서 이미 채워 두었습니다** — `sync.js` 맨 위가 아래처럼 되어 있습니다(이 프로젝트 값).
다른 프로젝트로 옮길 때만 Supabase → **Project Settings → API** 에서 두 값을 다시 복사해 바꿉니다.

```js
var CONFIG = {
  supabaseUrl: "https://qvhupdivtfzhzymovtyy.supabase.co",
  supabaseAnonKey: "sb_publishable_...",   // publishable(anon) 키 — 공개되어도 되고 RLS 가 지킵니다
  ...
};
```

- 두 값을 **비우면** 예전처럼 local 모드(이 기기에만 저장)로 돌아갑니다.
- 화면 확인용으로 잠깐 모드를 바꿀 때는 주소에 `?sync=local` 또는 `?sync=remote` 를 붙입니다.

> `service_role`(secret) 키는 절대 넣지 마세요. anon 키는 RLS 로 보호되므로 앱에 넣어도 됩니다.

### 5-5. 두 사람 연결하기
1. **A 폰**: 앱 열기 → 로그인 화면 → **처음이에요 · 계정 만들기** → 이메일/비밀번호 → 계정 생성
2. **A 폰 설정** → **내 초대 코드** 6자리 확인(예: `418 302`) → 상대에게 알려주기
3. **B 폰**: 같은 주소 열기 → 계정 만들기 → **설정 → 상대 초대 코드**에 A 의 6자리 입력 → **연결**
4. 끝. 이제 A 에서 일정을 추가하면 B 에 몇 초 안에 나타나고, 그 반대도 같습니다.

- B 폰에서는 이름·색의 "나/상대"가 자동으로 뒤집혀 보입니다(A 의 상대 = B 의 나).
- 연결을 끊으려면 **설정 → 커플 연결 해제**. 쌓인 기록은 남습니다.

---

## 6. 무엇이 저장되고 어디에 저장되나

| 데이터 | 로컬 모드 | 동기화 모드 |
|---|---|---|
| 커플·일정·노트·설정 | `localStorage["twolog:v1:state"]` | Supabase 테이블 5개 |
| 프로필 사진 | `localStorage["twolog:v1:state"]` 의 `couple.pics` | `settings` 행 `avatar:0`(만든 사람) · `avatar:1`(초대받은 사람) |
| 사진 원본 | **IndexedDB**(`twolog` DB, `photos` 스토어) | Supabase Storage `photos`(비공개) |
| 사진 보기 주소 | `URL.createObjectURL(blob)` | 6일짜리 **서명 URL** 을 열 때마다 재발급 |
| 보고 있던 탭·달력 위치 | `localStorage["twolog:v1:ui"]` (기기별, 동기화 안 함) | 같음 |
| 예전 기록 이전 여부 | — | `localStorage["twolog.migrated.<coupleId>"]` (기기별) |

- 프로필 사진은 256px 정사각 JPEG data URL(수십 KB)이라 `settings` 의 JSONB 한 칸에 그대로 들어갑니다. 사람마다 **행을 따로** 두어
  두 사람이 동시에 바꿔도 서로 덮어쓰지 않습니다. 상대가 바꾸면 Realtime 으로 몇 초 안에 이 폰에도 나타납니다.
- **로컬 기록 이전(v26)** 은 `localStorage` 를 읽기만 합니다. 사진 원본은 IndexedDB 에서 꺼내 Storage 로 올리고,
  이미 있는 기록은 같은 내용(날짜·제목 등)을 건너뛰므로 버튼을 두 번 눌러도 겹치지 않습니다.

- 사진은 넣기 전에 **긴 변 1800px · JPEG 0.82** 로 줄여 저장합니다(요즘 폰 사진 4MB → 대략 200~400KB).
- 저장은 150ms 모아서 하고, 앱이 가려지거나 닫힐 때(`pagehide`/`visibilitychange`) 바로 밀어 넣습니다.
- 오프라인에서 고친 내용도 다음 저장 때 다시 시도하고, 다시 연결되면 `online` 이벤트에서 재전송합니다.
- 상대 기기의 변경은 Realtime 구독으로 받아 450ms 디바운스 후 다시 읽어 화면에 반영합니다.

---

## 7. 코드 둘러보기 (sync.js)

`app.js` 는 데이터를 직접 만지지 않고 `TwoLog.createStore()` 가 준 store 만 씁니다.

```js
store.load()                  // 저장된 상태(+이 기기의 ui) 돌려주기
store.persist(S)              // 저장(디바운스) — 화면에서는 이 한 줄
store.flush()                 // 즉시 저장/전송
store.onRemote(doc => ...)    // 상대 기기 변경 수신
store.photos.add(file, meta)  // 압축 → IndexedDB 또는 Storage 업로드
store.photos.urls(photos)     // photo id → 볼 수 있는 주소
store.photos.remove(photo)    // 파일 삭제
store.auth.signIn/signUp/signOut
store.couple.myCode() / join(code) / leave()
store.avatar.set("me", dataUrl)     // v26: 내 프로필 사진을 서버(settings)로
store.local.summary()               // v26: 이 폰에 남은 예전 기록 요약
store.migrate.run({force:true})     // v26: 예전 기록 이어 오기 (자동 이전은 force 없이)
```

- 로컬 모드: `LocalBackend` (localStorage + IndexedDB).
- 동기화 모드: `SupabaseBackend` — 상태를 테이블 행으로 바꿔 **바뀐 행만** upsert/delete 하고,
  Realtime 을 구독합니다. supabase-js 는 필요할 때만 CDN 에서 ESM 으로 불러옵니다(빌드 불필요).
- 테이블 컬럼 설명은 `supabase-schema.sql` 주석에, 매핑 코드는 `stateToRows` / `rowsToState` 에 있습니다.

---

## 8. 알려진 한계 / 다음에 붙이면 좋은 것

- **두 사람 전용**입니다. `couples` 는 최대 2명(`members` 배열), 코드도 1회 연결용입니다.
- 푸시 알림이 없습니다. 알림이 필요하면 Web Push(서비스 워커 + VAPID)를 붙이면 됩니다.
- 가계부(지출) 화면은 이번 버전에서 뺐습니다. 데이터 구조(`expenses`)와 카테고리 색은 `app.js` 에 남겨 두어 화면만 다시 붙이면 됩니다.
- iOS 는 오래 안 쓰는 사이트의 저장소를 정리할 수 있습니다. 기록이 중요하면 동기화 모드를 권합니다.
- 사진 원본 화질이 필요하면 `sync.js` 의 `photoMaxDim` / `photoQuality` 를 올리세요(용량·전송 시간 증가).

---

## 9. 문제가 생기면

| 증상 | 확인 |
|---|---|
| 홈 화면에 추가했는데 주소창이 보임 | `manifest.json` 의 `display` 가 `standalone` 인지, 배포 주소가 https 인지 |
| 서비스 워커가 등록되지 않음 | `https` 또는 `localhost` 인지 (`http://아이피:8080` 은 등록 안 됨) |
| 로그인 후 "로그인이 필요해요" 만 보임 | Supabase Email Provider 켜짐 여부, Confirm email 설정, `CONFIG` 값 오타 |
| 동기화가 「오프라인 · 다시 연결하는 중」 | 5-2 의 스키마 SQL 을 아직 실행하지 않았을 수 있습니다(`public.couples` 없음). 앱은 멈추지 않고 이 기기 기록으로 계속 열립니다. SQL 실행 뒤 앱을 다시 열면 붙습니다. |
| 두 폰이 안 맞춰짐 | 두 사람이 **같은 커플**인지(설정 → 연결됨), Realtime 발행에 5개 테이블이 들어갔는지 |
| 사진이 안 보임 | Storage 버킷 `photos` 가 **비공개**이고 정책 4개가 생성됐는지, 서명 URL 만료(6일) 후 자동 갱신 |
| 예전 프로토타입 데이터가 보임 | `localStorage["couple-app-v1"]` 을 한 번 읽어 `twolog:v1:state` 로 옮깁니다(자동) |
| v25 에서 쓰던 기록이 새 계정에 안 보임 | v26 에서 로그인하면 자동으로 한 번 이어 옵니다. 안 보이면 My 탭 → 「폰에 있던 기록」 카드의 개수와 「폰에 있던 예전 기록 가져오기」 를 확인하세요(원격에 이미 기록이 있으면 자동 대신 이 버튼) |
| 상대 프로필 사진이 안 보임 | 사진은 `settings` 의 `avatar:0/1` 행에 있고 Realtime 발행에 `settings` 가 들어 있어야 합니다. 상대 사진은 그 사람이 자기 폰에서 바꿔야 합니다 |

### 자동 확인(테스트)

```bash
pip install playwright && playwright install chromium
python3 tests/v26.py       # v26: 폰에 있던 로컬 기록 자동 이전·중복 방지 · 프로필 사진 사람별 동기화 · local 회귀
python3 tests/v25.py       # v25: Supabase 연결(remote) — 로그인 화면 · 가입/로그인 · 초대 코드/연결 · 스키마 없을 때 · local 회귀
python3 tests/live.py      # 배포 주소가 방금 올린 버전을 서빙하는지(HTTP 200 · twolog-vNN · 콘솔 오류 없음)
python3 tests/smoke.py      # 5탭 · 일정 · 할일 · 사진 업로드/저장 · manifest · 서비스워커 · 새로 열어도 유지
python3 tests/v19.py        # v19: 컬러 시트 · 항목 이름 15px 검정 통일 · 확인 버튼 글씨 검정 · 노트 카드 탭→목록 · 꾹 눌러 이동 · 완료 항목 아래로 · 테두리 없는 달력 · 일정 검색 · 공휴일 빨강
python3 tests/v18.py        # v18: 홈 간격 · 사진첩 하루 3폴라로이드+뷰어 · 노트 탭 분리/글씨 · 이모지+이름 한 칸 · 꾹 눌러 순서 · 그날 타임라인 · 4자리 잠금 · PDF
python3 tests/v17.py        # (v17 기록용) 노트 「주제」 삭제 · 12색 팔레트 — v18 에서 바뀐 화면이라 지금은 일부 실패가 정상
```

마지막 확인 결과(v26): **390×844 헤드리스 Chromium 에서 콘솔/페이지 오류 0**,
v26(로컬 기록 이전·프로필 사진) 81 · v25(동기화·로그인·초대 코드) 43 · 스모크 18 · v18~v24 회귀 모두 **실패 0**.
v13~v17 은 그 뒤 화면이 바뀌어 지금은 일부 실패가 정상입니다(v26 이전에도 같은 항목이 실패).

---

## 10. 디자인 규칙 (깨지지 않게)

- 배경 **#FFFFFF** / 다크 **#111111**, 모서리 **전부 0px** (`border-radius:0` 강제 규칙이 CSS 끝에 있음)
  - 예외: 두 사람의 **프로필 사진 아바타는 동그라미** (`border-radius:50%`)
- **페이지 캡션 색** — 페이지마다 제목 줄 바탕색을 고를 수 있고, 글씨는 라이트·다크 모두 **#111111** 고정
- 강조색 코랄 `#D96B52`, 세이지 `#5F6F65`, 기본 일정색 소영 `#F7C6D4` · 상대 `#BCE0F7` · 공동 `#D6C5F7`
- 사진 캡션 글씨는 어떤 배경색을 골라도 **#111111** 고정
- 확인·기본 버튼(`완료`·`저장하기`·`추가하기` … `.btn-primary`)의 글씨는 컬러가 칠해져도 **검정 #111111** (검정에 가까운 아주 어두운 색만 흰 글씨)
- 홈에는 사진첩 미리보기를 두지 않습니다(사진은 사진첩 탭에서만)
- **노트 카드**는 「제목 → To-do」 순서만 둡니다(v17 에서 「이번 주 / 주제」 줄·칸 삭제)
- **노트 카드 안의 동그라미·항목은 체크 버튼이 아닙니다** — 카드 어디를 눌러도 그 리스트의 상세 목록이 열리고, 체크/해제는 들어간 목록 안에서만 합니다(v19)
- **완료된 항목은 늘 아래로** — 카드 미리보기·상세 목록·커스텀 리스트 모두 `byDone` 정렬, 체크하면 바로 내려가고 살짝 애니메이션됩니다(v19)
- **항목 이름(라벨) 글씨는 앱 전체 15px·700, 색은 검정**(`--lbl-fs`/`--lbl-fw`/`var(--ink)`: `.f > label`·`.cp-hd`·`.todo-label`·`.set-lbl`)
- **달력은 테두리·세로 격자선 없이** 트여 있고, 주 사이에만 옅은 가로선(`var(--line-2)`)을 긋습니다. 선택한 날은 테두리 대신 **어두운 바탕 + 반전 글씨**, 오늘은 숫자 색과 작은 점으로만 표시(v19)
- **달력 상단은 월 표시 가운데 + 양사이드 화살표 + 오른쪽 끝 일정 검색**(`data-act="calSearch"`), 하단 날짜는 `2026년 11월 17일 (화)` 처럼 18.5px·800 으로 크게(v19)
- **공휴일 숫자·이름은 빨강** `--hol` (라이트 `#D94848` · 다크 `#E86A6A`)
- **사진첩**은 앨범이 아니라 **날짜별**(최신순)로 묶고, 하루 사진은 흰 폴라로이드(위·옆 6px, 아래 18px 턱)를
  −3°·2°·−1.5°·3° 로 살짝 기울여 3열로 겹쳐 놓습니다. 다크 모드 프레임은 `#232326`
- **제목 줄 색 팔레트**는 12색(`#F2CFC9` … `#C4B28E`) 4열 3줄이고, 고른 색은 `--btn-bg`/`--btn-ink` 로
  모든 시트의 기본 버튼(저장하기·완료·추가하기·Add·연결하기)에 함께 적용됩니다
- **노트 상단 탭**(메모·버킷리스트·영화·먹방)은 한 덩어리 `.seg` 가 아니라 **각각 독립된 네모 칸**(`.segs`, 간격 8px,
  높이 44px, 글씨 15.5px)이고, 카드 제목 캡션은 17px 입니다. 탭 이름·리스트 이름은 **이모지와 이름을 한 칸**에 적습니다(`📝 메모`)
- **사진첩은 하루에 폴라로이드 3개까지** — 넘치면 세 번째 카드에 `+N`, 누르면 그날 사진이 크게 열리고 좌우로 넘겨 봅니다(`.pview`)
- **캘린더에서 날짜를 누르면** 그날의 일정 + 메모 카드 + 영화·먹방 기록 + 폴라로이드가 한 타임라인으로 이어집니다
- **노트 카드와 To-do 한 줄은 꾹 눌러(320ms) 순서를 바꿉니다** — 손을 떼면 `S.groups`/`S.lists` 순서로 저장됩니다
- **화면 잠금**은 My 탭에서 켜는 **4자리 숫자 잠금**입니다(기기 안에서만 확인하는 간단한 잠금, 기록 암호화 아님)
- **프로필 사진은 각자 자기 것만** — 두 사람이 연결된 뒤에는 My 탭에서도 상대 사진에 버튼이 없고(「○○ 폰에서 바꿔요」),
  사진은 `couple.pics` → settings `avatar:<slot>` 으로 사람별 저장되어 상대 폰에도 함께 보입니다(v26)
- **기록 PDF**는 My 탭 → 기간 선택 → 인쇄 창에서 ‘PDF로 저장’. 인쇄용 레이아웃은 `@media print` + `#printRoot` 만 남깁니다
- **서비스 워커**는 `skipWaiting` + `clients.claim` + 옛 캐시 삭제, 앱은 `controllerchange` 때 한 번만 새로고침합니다
