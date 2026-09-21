# 광명교회 홈페이지 이전

기존 광명교회 사이트를 바탕으로 만든 새 홈페이지입니다. 메인 화면과 공개 하위 메뉴 40개의 첫 화면을 로컬 파일로 저장했습니다. 로고와 공개 사진도 로컬에 포함되어 있어 기존 서버의 이미지 주소에 의존하지 않습니다.

## 현재 상태

- 메인 화면, 전체 메뉴, 소개 페이지, 예배 안내와 공개 목록 화면을 확인할 수 있습니다.
- 게시판과 영상 목록의 **첫 화면**을 보관했습니다. 상세 글, 이전 목록, 첨부파일은 아직 기존 사이트로 연결됩니다.
- 로그인, 회원가입, 게시글 작성, 관리자 기능은 아직 이전되지 않았습니다.
- 원본 DB와 업로드 파일 백업을 받으면 전체 게시물과 자료를 이전할 수 있습니다. 백업 파일과 비밀번호를 이 공개 저장소에 올리지 마세요.

## 로컬 실행

이 폴더에서 `python -m http.server 4173`으로 실행한 뒤 `http://localhost:4173/`을 엽니다. 배포용 파일은 별도 빌드 없이 사용할 수 있습니다.

## GitHub Pages

현재 **Deploy from a branch**, `main`, `/ (root)`로 게시 중입니다. 공개 주소는 https://donggil113.github.io/kmchurch-site/ 입니다.

구매한 `junim-whitestone.com`은 Cloudflare에서 DNS를 관리합니다. Cloudflare 계정에 로그인한 뒤 GitHub 저장소 **Settings → Pages → Custom domain**에 `junim-whitestone.com`을 저장하고, Cloudflare **DNS → Records**에 루트(`@`) A 레코드 `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`과 `www` CNAME `donggil113.github.io`를 추가하세요. 처음에는 각 레코드를 **DNS only**로 두고, GitHub DNS 검사와 HTTPS 인증서 발급 후 **Enforce HTTPS**를 확인하세요. DNS 연결 전에는 GitHub 주소가 새 도메인으로 이동해 접속에 실패할 수 있으므로 두 설정을 연달아 완료해야 합니다.

GitHub Pages는 서버 프로그램과 데이터베이스를 실행하지 않습니다. 회원·게시판·관리자 기능까지 운영하려면 별도 백엔드가 필요합니다.

## GitHub에서 직접 수정하기

1. https://github.com/donggil113/kmchurch-site 에 로그인하여 **Code**에서 바꿀 파일을 엽니다.
2. 파일 오른쪽 위 연필 아이콘(**Edit this file**)을 눌러 수정합니다.
3. **Commit changes**를 눌러 `main`에 저장하면 GitHub Pages가 자동으로 다시 게시합니다. 반영에는 몇 분이 걸릴 수 있습니다.

메인 글과 링크는 `index.html`, 디자인은 `styles.css`와 `archive.css`, 메뉴 동작은 `app.js`, 하위 화면은 `pages/`, 사진은 `assets/`에 있습니다. 사진은 **Add file → Upload files**로 올린 후 해당 HTML의 이미지 `src`를 새 경로로 바꾸세요. 여러 파일을 한 번에 고칠 때는 저장소 화면에서 `.` 키를 눌러 웹 편집기를 열 수 있습니다.

`pages/*.html`은 `scripts/snapshot_public.py`로 생성된 파일이므로 스크립트를 다시 실행하면 수동 수정이 덮어써질 수 있습니다. 회원·게시판 운영 기능은 HTML 파일 편집만으로 추가할 수 없습니다.

## 공개 화면 다시 가져오기

`scripts/snapshot_public.py`는 원본 사이트의 공개 화면과 이미지로 40개 페이지를 다시 생성합니다. 이 스크립트는 관리자 데이터나 비공개 첨부파일을 가져오지 않습니다.
