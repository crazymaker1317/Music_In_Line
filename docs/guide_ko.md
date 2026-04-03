# 🎼 Music In Line — 설치·실행·테스트 가이드 (Windows / Python)

> 이 문서는 Windows 환경에서 Music In Line 프로토타입을 **처음부터 직접 설치하고 실행·테스트**하는 전체 과정을 안내합니다.
> macOS/Linux 사용자도 동일한 순서를 따를 수 있으며, 해당 OS 전용 명령어를 함께 표기했습니다.

---

## 📑 목차

1. [사전 준비 — Python 설치](#1-사전-준비--python-설치)
2. [프로젝트 다운로드](#2-프로젝트-다운로드)
3. [가상환경 생성 및 활성화](#3-가상환경-생성-및-활성화)
4. [의존성 패키지 설치](#4-의존성-패키지-설치)
5. [단위 테스트 실행](#5-단위-테스트-실행)
6. [Gradio 웹 앱 실행](#6-gradio-웹-앱-실행)
7. [앱 사용 방법 — 단계별 워크플로우](#7-앱-사용-방법--단계별-워크플로우)
8. [핵심 모듈 직접 테스트 (스크립트)](#8-핵심-모듈-직접-테스트-스크립트)
9. [문제 해결 (FAQ)](#9-문제-해결-faq)
10. [프로젝트 구조 요약](#10-프로젝트-구조-요약)

---

## 1. 사전 준비 — Python 설치

### 1-1. Python 3.10 이상 설치

1. [python.org/downloads](https://www.python.org/downloads/) 에서 **Python 3.10 이상** 설치 파일을 다운로드합니다.
2. 설치 시 **"Add python.exe to PATH"** 체크박스를 반드시 선택하세요.
3. 설치 완료 후 명령 프롬프트(cmd) 또는 PowerShell을 열고 버전을 확인합니다.

```powershell
python --version
```

출력 예시:
```
Python 3.11.9
```

> ⚠️ `python`이 인식되지 않으면 환경 변수 PATH에 Python 경로가 추가되어 있는지 확인하세요.

### 1-2. pip 버전 확인

```powershell
pip --version
```

출력 예시:
```
pip 24.0 from C:\Users\<사용자>\AppData\Local\Programs\Python\Python311\Lib\site-packages\pip (python 3.11)
```

---

## 2. 프로젝트 다운로드

### 방법 A: Git 클론 (추천)

```powershell
git clone https://github.com/crazymaker1317/Music_In_Line.git
cd Music_In_Line
```

### 방법 B: ZIP 다운로드

1. GitHub 저장소 페이지에서 **Code → Download ZIP** 을 클릭합니다.
2. 다운로드된 ZIP 파일을 원하는 위치에 압축 해제합니다.
3. 명령 프롬프트에서 해당 폴더로 이동합니다.

```powershell
cd C:\Users\<사용자>\Downloads\Music_In_Line-main
```

---

## 3. 가상환경 생성 및 활성화

Python 가상환경을 사용하면 시스템 전역 패키지와 격리된 독립적인 환경에서 작업할 수 있습니다.

### 3-1. 가상환경 생성

```powershell
python -m venv mil
```

> `mil`은 가상환경 폴더 이름입니다. 원하는 이름으로 변경 가능합니다.

### 3-2. 가상환경 활성화

**Windows (PowerShell)**:
```powershell
mil\Scripts\Activate.ps1
```

**Windows (cmd)**:
```cmd
mil\Scripts\activate.bat
```

**macOS / Linux**:
```bash
source mil/bin/activate
```

활성화되면 프롬프트 앞에 `(mil)` 표시가 나타납니다:
```
(mil) C:\Users\<사용자>\Music_In_Line>
```

> 💡 PowerShell에서 스크립트 실행이 차단되면 아래 명령을 먼저 실행하세요:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### 3-3. 가상환경 비활성화 (작업 종료 시)

```powershell
deactivate
```

---

## 4. 의존성 패키지 설치

가상환경이 활성화된 상태에서 아래 명령을 실행합니다:

```powershell
pip install -r requirements.txt
```

### 설치되는 패키지 목록

| 패키지 | 버전 요구 | 용도 |
|---|---|---|
| `gradio` | ≥ 4.0.0 | 웹 UI 프레임워크 |
| `midiutil` | ≥ 1.2.1 | MIDI 파일 생성 |
| `matplotlib` | ≥ 3.7.0 | 선 변환 결과 시각화 |
| `numpy` | ≥ 1.24.0 | 이미지 데이터 처리 |
| `pytest` | ≥ 7.0.0 | 단위 테스트 프레임워크 |

설치가 완료되면 확인:
```powershell
pip list
```

`gradio`, `midiutil`, `matplotlib`, `numpy`, `pytest`가 목록에 있으면 성공입니다.

---

## 5. 단위 테스트 실행

프로젝트가 정상적으로 설치되었는지 **단위 테스트로 확인**합니다.

### 5-1. 전체 테스트 실행

```powershell
python -m pytest tests/ -v
```

### 5-2. 기대 출력

```
tests/test_line_simplifier.py::TestSimplifyLine::test_empty_input PASSED
tests/test_line_simplifier.py::TestSimplifyLine::test_single_point PASSED
tests/test_line_simplifier.py::TestSimplifyLine::test_two_points PASSED
tests/test_line_simplifier.py::TestSimplifyLine::test_straight_line PASSED
tests/test_line_simplifier.py::TestSimplifyLine::test_zigzag_line PASSED
tests/test_line_simplifier.py::TestSimplifyLine::test_complex_curve PASSED
tests/test_line_simplifier.py::TestSimplifyLine::test_epsilon_zero PASSED
tests/test_line_simplifier.py::TestEnforceLeftToRight::test_empty_input PASSED
tests/test_line_simplifier.py::TestEnforceLeftToRight::test_already_increasing PASSED
tests/test_line_simplifier.py::TestEnforceLeftToRight::test_backward_movement PASSED
tests/test_line_simplifier.py::TestEnforceLeftToRight::test_single_point PASSED
tests/test_note_arranger.py::TestArrangeNotes::test_empty_input PASSED
tests/test_note_arranger.py::TestArrangeNotes::test_single_point PASSED
tests/test_note_arranger.py::TestArrangeNotes::test_simple_straight_line PASSED
tests/test_note_arranger.py::TestArrangeNotes::test_different_time_signatures PASSED
tests/test_note_arranger.py::TestArrangeNotes::test_note_pitches_in_range PASSED
tests/test_note_arranger.py::TestArrangeNotes::test_note_has_positive_duration PASSED
tests/test_note_arranger.py::TestNotesToText::test_empty_notes PASSED
tests/test_note_arranger.py::TestNotesToText::test_single_note PASSED
tests/test_note_arranger.py::TestNotesToText::test_multiple_measures PASSED
tests/test_pitch_mapper.py::TestMapYToPitch::test_top_of_canvas PASSED
tests/test_pitch_mapper.py::TestMapYToPitch::test_bottom_of_canvas PASSED
tests/test_pitch_mapper.py::TestMapYToPitch::test_middle_of_canvas PASSED
tests/test_pitch_mapper.py::TestMapYToPitch::test_result_in_c_major_scale PASSED
tests/test_pitch_mapper.py::TestMapYToPitch::test_result_in_range PASSED
tests/test_pitch_mapper.py::TestMapYToPitch::test_invalid_canvas_height PASSED
tests/test_pitch_mapper.py::TestMapYToPitch::test_y_out_of_bounds_clamp PASSED
tests/test_pitch_mapper.py::TestPitchToNoteName::test_middle_c PASSED
tests/test_pitch_mapper.py::TestPitchToNoteName::test_a4 PASSED
tests/test_pitch_mapper.py::TestPitchToNoteName::test_c6 PASSED
tests/test_pitch_mapper.py::TestGetScalePitches::test_c_major_range PASSED
tests/test_pitch_mapper.py::TestGetScalePitches::test_unsupported_scale PASSED

============================== 32 passed ==============================
```

**32개 테스트가 모두 `PASSED`** 로 표시되면 정상입니다.

### 5-3. 테스트 파일별 설명

| 테스트 파일 | 테스트 수 | 검증 대상 |
|---|---|---|
| `test_line_simplifier.py` | 11개 | RDP 알고리즘 (빈 입력, 직선, 지그재그, 복잡한 곡선) + 좌→우 보정 |
| `test_note_arranger.py` | 9개 | 음표 배열 (빈 입력, 다양한 박자, pitch 범위, duration 유효성) |
| `test_pitch_mapper.py` | 12개 | Y좌표→MIDI pitch 매핑 (경계값, C 메이저 스케일, 음 이름 변환) |

### 5-4. 특정 테스트 파일만 실행

```powershell
# 선 단순화 테스트만
python -m pytest tests/test_line_simplifier.py -v

# 음높이 매핑 테스트만
python -m pytest tests/test_pitch_mapper.py -v

# 음표 배열 테스트만
python -m pytest tests/test_note_arranger.py -v
```

---

## 6. Gradio 웹 앱 실행

### 6-1. 앱 시작

```powershell
python app.py
```

### 6-2. 기대 출력

```
Running on local URL:  http://127.0.0.1:7860

To create a public link, set `share=True` in `launch()`.
```

### 6-3. 브라우저에서 접속

터미널에 표시된 URL(`http://127.0.0.1:7860`)을 브라우저(Chrome, Edge 등)에서 열면 Music In Line 앱이 나타납니다.

### 6-4. 앱 종료

터미널에서 `Ctrl + C`를 눌러 서버를 종료합니다.

---

## 7. 앱 사용 방법 — 단계별 워크플로우

### Step 1: 선 그리기 🎨

1. 화면 상단의 **"선 그리기 캔버스"** 영역에 마우스로 선을 그립니다.
2. **왼쪽에서 오른쪽**으로 자유롭게 그려주세요.
   - **가로축** = 시간 (왼쪽 → 오른쪽으로 시간이 흐름)
   - **세로축** = 음높이 (위 = 높은 음, 아래 = 낮은 음)
3. 선을 다양하게 올리고 내리면 음높이가 다양한 멜로디가 생성됩니다.

### Step 2: 선 변환하기 📐

1. **"단순화 정도 (epsilon)"** 슬라이더를 조절합니다.
   - 값이 작을수록(1에 가까울수록) 원본에 가깝게 유지
   - 값이 클수록(30에 가까울수록) 더 단순한 직선으로 변환
   - **기본값 5**를 추천합니다.
2. **"📐 선 변환하기"** 버튼을 클릭합니다.
3. 아래에 **변환 결과 시각화** 그래프가 표시됩니다:
   - 파란색 = 원본 곡선
   - 빨간색 = 단순화된 직선 (꺾이는 점이 빨간 점으로 표시)
   - 회색 점선 = 마디 구분선

### Step 3: 설정 조절 ⚙️

| 설정 항목 | 범위 | 기본값 | 설명 |
|---|---|---|---|
| **박자 선택** | 4/4, 3/4, 2/4 | 4/4 | 마디당 박 수 결정 |
| **마디 수** | 2 ~ 8 | 4 | 전체 음악의 길이 |
| **BPM (빠르기)** | 60 ~ 180 | 120 | 음악의 빠르기 (높을수록 빠름) |

### Step 4: 음악 생성하기 🎵

1. **"🎵 음악 생성하기"** 버튼을 클릭합니다.
2. 하단에 두 가지 결과가 표시됩니다:
   - **📝 음표 텍스트 정보**: 마디별 음표 이름, 종류, 시작 위치가 표시됩니다.
   - **🔊 MIDI 파일 다운로드**: 생성된 MIDI 파일을 다운로드할 수 있습니다.

### Step 5: 박자 변경하여 재생성 🔄

1. **박자 선택**을 다른 값(예: 3/4, 2/4)으로 변경합니다.
2. **"🎵 음악 생성하기"** 버튼을 다시 클릭합니다.
3. **선을 다시 그릴 필요 없이** 같은 선 데이터에서 새로운 박자의 음악이 생성됩니다.

> 💡 같은 선이라도 박자에 따라 리듬과 음표 배치가 달라지는 것을 비교해 보세요!

---

## 8. 핵심 모듈 직접 테스트 (스크립트)

Gradio UI 없이 각 모듈을 직접 Python 스크립트로 테스트할 수 있습니다.

### 8-1. 전체 파이프라인 테스트

아래 코드를 Python 인터프리터에서 실행하거나, 파일로 저장 후 `python 파일이름.py`로 실행하세요:

```python
from core.line_simplifier import simplify_line
from core.note_arranger import arrange_notes, notes_to_text
from core.midi_generator import generate_midi

# 1. 샘플 좌표 데이터 (선을 시뮬레이션)
points = [
    (0, 100), (100, 300), (200, 50), (300, 250),
    (400, 150), (500, 350), (600, 100), (700, 200), (800, 300)
]

# 2. 선 단순화 (epsilon=5)
simplified = simplify_line(points, epsilon=5.0)
print(f"원본: {len(points)}개 → 단순화: {len(simplified)}개")

# 3. 음표 배열 (4/4 박자, 4마디)
notes = arrange_notes(
    simplified,
    canvas_width=800,
    canvas_height=400,
    time_signature=(4, 4),
    num_measures=4
)
print(f"\n생성된 음표: {len(notes)}개")
print(notes_to_text(notes))

# 4. MIDI 파일 생성
midi_path = generate_midi(notes, bpm=120, output_path="output/test_result.mid")
print(f"\nMIDI 파일 생성 완료: {midi_path}")
```

### 8-2. 기대 출력 (예시)

```
원본: 9개 → 단순화: 8개

생성된 음표: 7개

--- 마디 1 ---
  F5 - 2분음표 (시작: 0.0박)
  F4 - 2분음표 (시작: 2.0박)

--- 마디 2 ---
  A5 - 2분음표 (시작: 0.0박)
  A4 - 2분음표 (시작: 2.0박)

--- 마디 3 ---
  D5 - 2분음표 (시작: 0.0박)
  D4 - 2분음표 (시작: 2.0박)

--- 마디 4 ---
  F5 - 온음표 (시작: 0.0박)

MIDI 파일 생성 완료: output/test_result.mid
```

### 8-3. 박자별 비교 테스트

```python
from core.line_simplifier import simplify_line
from core.note_arranger import arrange_notes, notes_to_text

points = [(0, 100), (200, 300), (400, 50), (600, 250), (800, 150)]
simplified = simplify_line(points, epsilon=5.0)

for ts_name, ts in [("4/4", (4, 4)), ("3/4", (3, 4)), ("2/4", (2, 4))]:
    notes = arrange_notes(simplified, 800, 400, ts, 4)
    print(f"\n{'='*40}")
    print(f"박자: {ts_name}")
    print(f"{'='*40}")
    print(notes_to_text(notes))
```

---

## 9. 문제 해결 (FAQ)

### Q1. `python`이 인식되지 않습니다

**원인**: Python이 시스템 PATH에 등록되지 않았습니다.

**해결**: Python 설치 시 "Add python.exe to PATH" 옵션을 체크하지 않은 경우:
1. **Windows 설정 → 시스템 → 정보 → 고급 시스템 설정 → 환경 변수**
2. **Path** 변수에 Python 설치 경로를 추가합니다 (예: `C:\Users\<사용자>\AppData\Local\Programs\Python\Python311\`)
3. 명령 프롬프트를 다시 열고 `python --version`으로 확인합니다.

또는 Python을 다시 설치하면서 "Add python.exe to PATH"를 체크합니다.

### Q2. `pip install` 시 권한 오류가 발생합니다

**해결**: 가상환경을 활성화한 상태에서 실행하고 있는지 확인하세요. 프롬프트 앞에 `(mil)`이 표시되어야 합니다.

### Q3. PowerShell에서 가상환경 활성화 스크립트가 차단됩니다

**해결**:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Q4. `gradio` 설치 중 오류가 발생합니다

**해결**: pip를 최신 버전으로 업그레이드한 후 다시 시도하세요:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Q5. 앱 실행 시 포트 충돌이 발생합니다

**해결**: 다른 포트를 지정하여 실행할 수 있습니다. `app.py`의 마지막 줄을 수정합니다:
```python
app.launch(server_port=7861)
```

### Q6. MIDI 파일을 재생하려면 어떻게 하나요?

다운로드한 `.mid` 파일을 다음 방법으로 재생할 수 있습니다:
- **Windows Media Player**: 파일을 더블클릭하여 재생
- **온라인 재생기**: [signal.vercel.app/edit](https://signal.vercel.app/edit) 등의 웹 MIDI 재생기에 파일을 업로드
- **MuseScore**: 무료 악보 소프트웨어로 악보 확인 및 재생 가능

### Q7. 테스트가 실패합니다

**해결**: 의존성이 올바르게 설치되었는지 확인하세요:
```powershell
pip install -r requirements.txt
python -m pytest tests/ -v
```

그래도 실패하면 가상환경을 삭제하고 다시 생성하세요:
```powershell
deactivate
rmdir /s /q mil
python -m venv mil
mil\Scripts\activate.bat
pip install -r requirements.txt
python -m pytest tests/ -v
```

---

## 10. 프로젝트 구조 요약

```
Music_In_Line/
├── app.py                      # Gradio 웹 앱 메인 진입점
├── core/                       # 핵심 로직 모듈
│   ├── __init__.py
│   ├── line_simplifier.py      # 곡선 → 직선 변환 (RDP 알고리즘)
│   ├── pitch_mapper.py         # Y좌표 → MIDI pitch 매핑
│   ├── note_arranger.py        # 직선 데이터 → 음표 배열
│   └── midi_generator.py       # 음표 → MIDI 파일 생성
├── utils/                      # 유틸리티
│   ├── __init__.py
│   └── visualization.py        # matplotlib 시각화
├── tests/                      # 단위 테스트 (32개)
│   ├── test_line_simplifier.py # 선 단순화 테스트 (11개)
│   ├── test_pitch_mapper.py    # 음높이 매핑 테스트 (12개)
│   └── test_note_arranger.py   # 음표 배열 테스트 (9개)
├── output/                     # MIDI 파일 출력 폴더
├── docs/
│   └── guide_ko.md             # ← 이 문서
├── requirements.txt            # Python 의존성 목록
├── README.md                   # 프로젝트 소개 (한글)
└── TODO.md                     # 향후 작업 목록
```

---

## 📌 빠른 시작 요약 (TL;DR)

```powershell
# 1. 프로젝트 다운로드
git clone https://github.com/crazymaker1317/Music_In_Line.git
cd Music_In_Line

# 2. 가상환경 생성 및 활성화
python -m venv mil
mil\Scripts\activate.bat          # Windows cmd
# mil\Scripts\Activate.ps1        # Windows PowerShell
# source mil/bin/activate         # macOS / Linux

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 테스트 실행 (32개 모두 PASSED 확인)
python -m pytest tests/ -v

# 5. 앱 실행
python app.py
# → 브라우저에서 http://127.0.0.1:7860 접속
```
