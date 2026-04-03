# 🎵 Music In Line — 설치 및 실행 가이드

> 윈도우(Windows) 환경에서 Python을 사용하여 프로젝트를 설치하고, 실행하고, 테스트하는 전체 과정을 안내합니다.

---

## 📋 목차

1. [사전 요구사항](#1-사전-요구사항)
2. [프로젝트 다운로드](#2-프로젝트-다운로드)
3. [가상 환경 설정](#3-가상-환경-설정)
4. [의존성 패키지 설치](#4-의존성-패키지-설치)
5. [테스트 실행](#5-테스트-실행)
6. [애플리케이션 실행](#6-애플리케이션-실행)
7. [사용 방법](#7-사용-방법)
8. [프로젝트 구조](#8-프로젝트-구조)
9. [문제 해결 (Troubleshooting)](#9-문제-해결-troubleshooting)

---

## 1. 사전 요구사항

### Python 설치

- **Python 3.10 이상**이 필요합니다. (3.12 권장)
- [python.org](https://www.python.org/downloads/) 에서 최신 버전을 다운로드하세요.
- 설치 시 **"Add Python to PATH"** 체크박스를 반드시 선택하세요.

설치 확인:

```powershell
python --version
# 출력 예: Python 3.12.x
```

### Git 설치

- [git-scm.com](https://git-scm.com/download/win) 에서 Git을 설치하세요.

설치 확인:

```powershell
git --version
# 출력 예: git version 2.x.x
```

---

## 2. 프로젝트 다운로드

PowerShell 또는 명령 프롬프트(CMD)를 열고, 원하는 작업 디렉터리에서 실행합니다:

```powershell
git clone https://github.com/crazymaker1317/Music_In_Line.git
cd Music_In_Line
```

---

## 3. 가상 환경 설정

Python 가상 환경을 생성하여 시스템 패키지와 격리된 환경에서 작업합니다.

```powershell
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화 (PowerShell)
.\venv\Scripts\Activate.ps1

# 가상 환경 활성화 (CMD)
.\venv\Scripts\activate.bat
```

> **참고:** PowerShell에서 스크립트 실행이 제한된 경우, 아래 명령을 먼저 실행하세요:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

활성화에 성공하면 프롬프트 앞에 `(venv)`가 표시됩니다:

```
(venv) PS C:\Users\...\Music_In_Line>
```

---

## 4. 의존성 패키지 설치

가상 환경이 활성화된 상태에서 필요한 패키지를 설치합니다:

```powershell
pip install -r requirements.txt
```

### 설치되는 주요 패키지

| 패키지 | 버전 요구사항 | 용도 |
|--------|-------------|------|
| `gradio` | ≥ 6.7.0 | 웹 UI (Sketchpad 캔버스, 오디오 플레이어) |
| `mido` | ≥ 1.3.0 | MIDI 프로토콜 처리 |
| `pretty_midi` | ≥ 0.2.10 | MIDI 파일 생성 및 사인파 합성 |
| `numpy` | ≥ 1.26.0 | 수치 계산 (좌표 정규화, 오디오 배열) |
| `scipy` | ≥ 1.12.0 | WAV 파일 저장 |

테스트를 위해 `pytest`도 함께 설치합니다:

```powershell
pip install pytest
```

설치 확인:

```powershell
pip list | findstr "gradio mido pretty-midi numpy scipy pytest"
```

---

## 5. 테스트 실행

프로젝트에는 51개의 단위 테스트가 포함되어 있습니다. 모든 테스트를 실행하여 설치가 올바른지 확인하세요.

### 전체 테스트 실행

```powershell
python -m pytest tests/ -v
```

### 예상 출력

```
tests/test_app.py::TestExtractCoordinatesFromImage::test_none_input PASSED
tests/test_app.py::TestExtractCoordinatesFromImage::test_blank_white_image PASSED
...
tests/test_core.py::TestProcessLine::test_summary_contains_note_names PASSED

========================= 51 passed in x.xxs =========================
```

모든 테스트가 `PASSED`로 표시되면 설치가 정상적으로 완료된 것입니다.

### 개별 모듈 테스트

특정 모듈만 테스트하고 싶은 경우:

```powershell
# 핵심 음악 처리 로직 테스트 (31개)
python -m pytest tests/test_core.py -v

# 오디오/MIDI 생성 테스트 (10개)
python -m pytest tests/test_audio.py -v

# Gradio 앱 콜백 테스트 (10개)
python -m pytest tests/test_app.py -v
```

---

## 6. 애플리케이션 실행

### 웹 서버 시작

```powershell
python app.py
```

### 예상 출력

```
* Running on local URL:  http://127.0.0.1:7860
* To create a public link, set `share=True` in `launch()`.
```

### 브라우저에서 접속

웹 브라우저에서 아래 주소를 엽니다:

```
http://127.0.0.1:7860
```

> **팁:** 대부분의 경우 서버가 시작되면 브라우저가 자동으로 열립니다.

### 서버 종료

터미널에서 `Ctrl + C`를 눌러 서버를 종료합니다.

---

## 7. 사용 방법

### 기본 워크플로우

1. **그리기:** 왼쪽 캔버스에서 브러시(🖌) 도구를 선택한 후, 마우스로 선을 그립니다.
   - **세로 위치** → 음의 높낮이 (위쪽 = 높은 음, 아래쪽 = 낮은 음)
   - **가로 위치** → 시간 흐름 (왼쪽 = 시작, 오른쪽 = 끝)

2. **모드 선택:** 오른쪽 패널에서 작곡 모드를 선택합니다.
   - **Rule-based:** 그린 좌표를 C 장조(C Major) 음계에 맞춰 직접 변환합니다.
   - **AI-Assisted:** Rule-based 결과에 경과음(Passing Tone)을 추가하여 멜로디를 부드럽게 합니다.

3. **생성:** "🎶 Generate Music" 버튼을 클릭합니다.

4. **결과 확인:**
   - **Audio Preview:** 생성된 멜로디를 바로 들을 수 있습니다.
   - **Download MIDI:** MIDI 파일(`.mid`)을 다운로드할 수 있습니다.
   - **Generated Notes:** 변환된 음표 목록이 텍스트로 표시됩니다.

### 음표 매핑 상세

| 매핑 | 입력 범위 | 출력 범위 | 설명 |
|------|----------|----------|------|
| Y축 → 음높이 | 0~256px | MIDI 48~72 (C3~C5) | 캔버스 위쪽 = 높은 음 |
| X축 → 시간 | 0~512px | 32개 16분음표 (120 BPM) | 캔버스 왼쪽 = 시작 |
| 음계 보정 | MIDI 48~72 | C 장조 음계 | C, D, E, F, G, A, B |

---

## 8. 프로젝트 구조

```
Music_In_Line/
├── app.py                    # Gradio 웹 애플리케이션 (진입점)
├── requirements.txt          # Python 의존성 목록
├── readme                    # 프로젝트 개요 (한국어/영어)
├── music_in_line/            # 핵심 라이브러리
│   ├── __init__.py
│   ├── core.py               # 좌표→MIDI 변환, 음계 스냅, 스무딩
│   └── audio.py              # MIDI 파일 생성, WAV 합성
├── tests/                    # 단위 테스트
│   ├── __init__.py
│   ├── test_core.py          # core.py 테스트 (31개)
│   ├── test_audio.py         # audio.py 테스트 (10개)
│   └── test_app.py           # app.py 테스트 (10개)
└── docs/                     # 문서
    └── guide_ko.md           # 이 문서
```

### 처리 파이프라인

```
사용자 그림 (Sketchpad)
    ↓
좌표 추출 (extract_coordinates_from_image)
    ↓  비흰색 픽셀 감지 → X열 그룹핑 → 평균 Y 계산 → 최대 64개 서브샘플링
    ↓
좌표 검증 (validate_coordinates)
    ↓  최소 2개 이상의 점 필요
    ↓
정규화 (normalize_coordinates)
    ↓  X→시간비율 [0,1], Y→음높이비율 [0,1] (Y축 반전)
    ↓
MIDI 매핑 (pitch_ratio_to_midi + snap_to_c_major)
    ↓  음높이 비율 → MIDI 48~72 → C 장조 스냅
    ↓
시간 매핑 (time_ratio_to_seconds)
    ↓  시간비율 → 16분음표 그리드 (120 BPM)
    ↓
[AI-Assisted 모드] 스무딩 (smooth_melody)
    ↓  4반음 초과 점프 → 경과음 삽입
    ↓
MIDI/WAV 생성 (events_to_midi + midi_to_wav)
    ↓
결과 출력 (오디오 미리듣기 + MIDI 다운로드 + 음표 요약)
```

---

## 9. 문제 해결 (Troubleshooting)

### `python`이 인식되지 않는 경우

```powershell
# Python이 PATH에 등록되어 있는지 확인
where python

# python3으로 시도
python3 --version
```

Python을 설치할 때 "Add Python to PATH"를 체크하지 않은 경우, 환경 변수에 수동으로 추가하거나 Python을 재설치하세요.

### PowerShell 스크립트 실행 정책 오류

```
.\venv\Scripts\Activate.ps1 : 이 시스템에서 스크립트를 실행할 수 없으므로...
```

해결 방법:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `pip install` 시 빌드 오류 (특히 `scipy`)

일부 패키지는 C 컴파일러가 필요할 수 있습니다. 아래 순서로 시도하세요:

1. pip를 최신 버전으로 업그레이드:
   ```powershell
   python -m pip install --upgrade pip
   ```
2. 바이너리 휠(wheel) 설치 확인:
   ```powershell
   pip install --only-binary=:all: scipy numpy
   ```
3. 그래도 실패하면 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 설치를 고려하세요.

### Gradio 서버가 시작되지 않는 경우

- 포트 7860이 이미 사용 중인지 확인:
  ```powershell
  netstat -ano | findstr 7860
  ```
- 다른 포트를 지정하여 실행:
  ```powershell
  python -c "from app import build_interface; build_interface().launch(server_port=7870)"
  ```

### 테스트가 실패하는 경우

- 가상 환경이 활성화되어 있는지 확인하세요 (프롬프트에 `(venv)` 표시).
- 의존성이 모두 설치되었는지 확인:
  ```powershell
  pip install -r requirements.txt pytest
  ```
- 특정 테스트만 상세하게 실행하여 오류 메시지를 확인:
  ```powershell
  python -m pytest tests/test_core.py -v --tb=long
  ```

---

## 🔗 빠른 참조 (Quick Reference)

```powershell
# 전체 설치 및 실행 (복사-붙여넣기용)
git clone https://github.com/crazymaker1317/Music_In_Line.git
cd Music_In_Line
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt pytest
python -m pytest tests/ -v
python app.py
```
