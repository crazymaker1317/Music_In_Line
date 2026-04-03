# 🎵 Music In Line — 프로젝트 가이드

> **"삐죽삐죽한 직선을 그리면 멜로디가 됩니다"**
>
> 사용자가 캔버스에 그린 선(polyline)을 MIDI 멜로디로 변환하는 Gradio 기반 웹 애플리케이션입니다.

---

## 목차

1. [현재 개발 내용 및 진척 상황](#1-현재-개발-내용-및-진척-상황)
2. [설치 방법 (Windows + Python 가상환경)](#2-설치-방법)
3. [실행 및 테스트 방법](#3-실행-및-테스트-방법)
4. [기타 사용자 대응 요소](#4-기타-사용자-대응-요소)

---

## 1. 현재 개발 내용 및 진척 상황

### 프로젝트 구조

```
Music_In_Line/
├── app.py                    # Gradio 웹 UI (메인 진입점)
├── music_in_line/            # 핵심 패키지
│   ├── __init__.py
│   ├── core.py               # 좌표 추출, 피크 검출, MIDI 매핑, 스무딩
│   └── audio.py              # MIDI 파일 생성, WAV 합성, 피아노 롤 시각화
├── tests/                    # 테스트 코드
│   ├── test_core.py          # core 모듈 테스트 (20개)
│   ├── test_audio.py         # audio 모듈 테스트 (12개)
│   └── test_app.py           # 앱 파이프라인 테스트 (5개)
├── requirements.txt          # Python 의존성 목록
├── .gitignore
└── docs/
    └── guide_ko.md           # 본 문서
```

### 구현 완료 기능 (v0.1 — PoC)

| 단계 | 기능 | 상태 |
|------|------|------|
| Phase 1 | 캔버스 입력 (`gr.Sketchpad`, 512×256, 흑백) | ✅ 완료 |
| Phase 1 | 이미지 → 좌표 변환 (threshold 128, x별 y 중앙값) | ✅ 완료 |
| Phase 1 | 입력 검증 (빈 캔버스, 점 2개 미만, 선 5개 미만 경고) | ✅ 완료 |
| Phase 2 | Peak/Valley 검출 (`scipy.signal.find_peaks`) | ✅ 완료 |
| Phase 2 | MIDI 매핑 (C4~C6, C Major 스케일 스냅핑) | ✅ 완료 |
| Phase 2 | 규칙 기반 스무딩 (경과음 삽입 + 최소 음표 길이 보정) | ✅ 완료 |
| Phase 3 | MIDI 파일 생성 (`pretty_midi`) | ✅ 완료 |
| Phase 3 | WAV 오디오 합성 (사인파 + ADSR 엔벨로프) | ✅ 완료 |
| Phase 3 | 피아노 롤 시각화 (`matplotlib`) | ✅ 완료 |
| UI | Gradio Blocks 레이아웃 (캔버스 + 모드 선택 + 출력) | ✅ 완료 |
| 테스트 | 37개 단위/통합 테스트 (전체 통과) | ✅ 완료 |

### 처리 파이프라인

```
사용자가 선을 그림
    ↓
gr.Sketchpad → image_dict (numpy 배열)
    ↓
extract_coordinates_from_image() → coords (N×2 배열, x 기준 정렬)
    ↓
detect_musical_peaks() → notes_data (꺾이는 점 리스트)
    ↓
map_to_midi() → midi_notes (MIDI 음표 리스트, C Major 스냅)
    ↓ (선택: smooth_melody)
create_midi() → PrettyMIDI 객체 → .mid 파일
midi_to_wav() → .wav 파일 (사인파 합성)
plot_piano_roll() → matplotlib Figure
    ↓
Gradio 출력: [피아노 롤 그림] + [오디오 재생기] + [MIDI 다운로드]
```

### 미구현 / 추후 확장 예정

| 버전 | 기능 | 비고 |
|------|------|------|
| v0.2 | 다양한 스케일 선택 (Minor, Pentatonic 등) | `gr.Dropdown` 추가 |
| v0.3 | 음색 개선 (피아노, 기타 등) | FluidSynth + GM SoundFont |
| v0.4 | AI 멜로디 보정 | Magenta `melody_rnn` 또는 경량 Transformer |
| v0.5 | 오선지 악보 시각화 | `music21` 라이브러리 |
| v0.6 | 다중 트랙 (화성) | 여러 선 → 여러 악기 동시 출력 |

---

## 2. 설치 방법

### 사전 요구사항

- **운영체제:** Windows 10/11 (macOS, Linux도 가능)
- **Python:** 3.10 이상 (3.11 권장)
- **Git:** 설치 필요 ([git-scm.com](https://git-scm.com/))

### 2-1. Python 설치 (Windows)

1. [python.org](https://www.python.org/downloads/) 에서 Python 3.11 다운로드
2. 설치 시 **"Add Python to PATH"** 체크 (중요!)
3. 설치 확인:
   ```cmd
   python --version
   ```
   `Python 3.11.x` 형태로 출력되면 성공입니다.

### 2-2. 프로젝트 클론

```cmd
git clone https://github.com/crazymaker1317/Music_In_Line.git
cd Music_In_Line
```

### 2-3. 가상환경 생성 및 활성화

Windows **명령 프롬프트(cmd)**:
```cmd
python -m venv mil
mil\Scripts\activate
```

Windows **PowerShell**:
```powershell
python -m venv mil
mil\Scripts\Activate.ps1
```

> **참고:** PowerShell에서 실행 정책 오류가 발생하면:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> 위 명령을 먼저 실행하세요.

macOS / Linux:
```bash
python3 -m venv mil
source mil/bin/activate
```

활성화 후 프롬프트 앞에 `(mil)`이 표시되면 성공입니다.

### 2-4. 의존성 설치

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

설치되는 패키지:

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `gradio` | ≥ 4.0.0 | 웹 UI (캔버스, 오디오 플레이어 등) |
| `pretty_midi` | ≥ 0.2.10 | MIDI 파일 생성 |
| `numpy` | ≥ 1.24.0 | 이미지 → 좌표 변환, 사인파 합성 |
| `scipy` | ≥ 1.12.0 | Peak 검출, WAV 파일 쓰기 |
| `matplotlib` | ≥ 3.7.0 | 피아노 롤 시각화 |

---

## 3. 실행 및 테스트 방법

### 3-1. 앱 실행 (Gradio)

가상환경이 활성화된 상태에서:

```cmd
python app.py
```

실행 후 콘솔에 다음과 같은 URL이 표시됩니다:
```
Running on local URL: http://127.0.0.1:7860
```

웹 브라우저에서 `http://127.0.0.1:7860` 을 열면 앱을 사용할 수 있습니다.

### 3-2. 앱 사용법

```
┌─────────────────────────────────────────────────────┐
│             🎵 Visual Composition Prototype          │
├───────────────────────────┬─────────────────────────┤
│                           │  ○ 기본 모드             │
│    [Drawing Canvas]       │  ○ 스무딩 적용           │
│    512 × 256 px           │                         │
│                           │  🎵 Generate Music       │
├───────────────────────────┴─────────────────────────┤
│  [Piano Roll Plot]                                  │
├─────────────────────────────────────────────────────┤
│  [Audio Player]   [MIDI Download]                   │
└─────────────────────────────────────────────────────┘
```

1. **캔버스에 선 그리기**: 마우스로 삐죽삐죽한 선을 자유롭게 그립니다.
   - 위쪽으로 올라가면 높은 음, 아래쪽으로 내려가면 낮은 음
   - 왼쪽에서 오른쪽으로 시간이 흐름 (총 4초)
2. **모드 선택**:
   - `기본 모드`: 꺾이는 점을 그대로 음표로 변환
   - `스무딩 적용`: 너무 큰 음정 도약에 경과음 삽입 + 짧은 음표 보정
3. **🎵 Generate Music** 버튼 클릭
4. **결과 확인**:
   - 피아노 롤(시각화)로 생성된 멜로디 확인
   - 오디오 플레이어로 직접 재생
   - MIDI 파일 다운로드 (다른 DAW에서 열기 가능)

### 3-3. 테스트 실행

가상환경이 활성화된 상태에서:

```cmd
pip install pytest
python -m pytest tests/ -v
```

현재 37개 테스트가 모두 통과합니다:

| 테스트 파일 | 테스트 수 | 대상 |
|-------------|-----------|------|
| `tests/test_core.py` | 20개 | 좌표 추출, 피크 검출, MIDI 매핑, 스무딩 |
| `tests/test_audio.py` | 12개 | MIDI 생성, WAV 합성, 피아노 롤 |
| `tests/test_app.py` | 5개 | 전체 파이프라인 (에러 처리 포함) |

특정 테스트만 실행하기:
```cmd
# core 모듈만
python -m pytest tests/test_core.py -v

# 특정 테스트 클래스만
python -m pytest tests/test_core.py::TestMapToMidi -v

# 특정 테스트 함수만
python -m pytest tests/test_core.py::TestMapToMidi::test_c_major_snap -v
```

---

## 4. 기타 사용자 대응 요소

### 알려진 제한사항

1. **사인파 음색**: 현재 WAV 출력은 순수 사인파로 합성되어, 실제 악기 소리와 다릅니다. 추후 FluidSynth + SoundFont로 개선 예정입니다.
2. **C Major 고정**: 현재는 C Major(다장조) 스케일만 지원합니다. 다른 스케일(단조, 펜타토닉 등)은 v0.2에서 추가 예정입니다.
3. **단일 트랙**: 한 번에 하나의 멜로디만 생성됩니다. 화성(하모니)은 v0.6에서 계획 중입니다.
4. **멜로디 길이 4초 고정**: 캔버스의 왼쪽 끝~오른쪽 끝이 0~4초로 매핑됩니다.

### 트러블슈팅

#### "pip" 명령을 찾을 수 없다는 오류

```cmd
python -m pip install -r requirements.txt
```
`pip` 대신 `python -m pip`을 사용하세요.

#### PowerShell 실행 정책 오류

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Gradio 실행 시 포트 충돌

```cmd
python app.py
```
기본 포트(7860)가 사용 중이면 Gradio가 자동으로 다른 포트를 선택합니다. 콘솔 출력에 표시된 URL을 확인하세요.

#### 가상환경 비활성화

작업을 마치면:
```cmd
deactivate
```

### 의존성 관련 참고

- 이 프로젝트는 **FluidSynth**, **Magenta**, **TensorFlow** 등 설치가 어려운 라이브러리를 의도적으로 사용하지 않습니다.
- `pip install -r requirements.txt` 한 줄이면 모든 의존성이 설치됩니다.
- 시스템 레벨 패키지(apt, brew 등) 설치가 별도로 필요하지 않습니다.

### 개발 참여 안내

코드를 수정한 후에는 반드시 테스트를 실행하여 기존 기능이 깨지지 않았는지 확인하세요:

```cmd
python -m pytest tests/ -v
```

주요 모듈별 역할:

| 파일 | 수정 시 확인 사항 |
|------|-------------------|
| `music_in_line/core.py` | `tests/test_core.py` 테스트 통과 여부 |
| `music_in_line/audio.py` | `tests/test_audio.py` 테스트 통과 여부 |
| `app.py` | `tests/test_app.py` 테스트 통과 + 브라우저에서 직접 확인 |
