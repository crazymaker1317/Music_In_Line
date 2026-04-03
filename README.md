# 🎼 Music In Line — 프로토타입

> **"내가 그린 선이 음악이 되는 마법!"**

Music In Line은 사용자가 캔버스에 선을 그리면, 해당 선을 분석하여 선택한 박자에 맞는 음악(MIDI)을 생성해주는 웹 애플리케이션입니다.

---

## 📖 프로젝트 소개

이 프로토타입은 **"선 → 데이터 변환 → 음표 배열 → MIDI 재생"**의 핵심 파이프라인이 동작하는 것을 검증하기 위해 제작되었습니다.

### 주요 기능
- 🎨 **선 그리기**: 웹 캔버스에 자유롭게 선을 그릴 수 있습니다
- 📐 **선 단순화**: Ramer-Douglas-Peucker 알고리즘으로 곡선을 직선 세그먼트로 변환합니다
- 🎵 **음표 배열**: 선택한 박자(4/4, 3/4, 2/4)에 맞게 음표를 자동 생성합니다
- 🔊 **MIDI 생성**: 생성된 음표를 MIDI 파일로 변환하여 다운로드할 수 있습니다
- 🔄 **박자 변경**: 같은 선으로 박자만 바꿔 새로운 음악을 생성할 수 있습니다

---

## 🛠️ 설치 방법

### 사전 요구 사항
- Python 3.10 이상

### 설치 순서

1. **저장소 클론**
```bash
git clone https://github.com/crazymaker1317/Music_In_Line.git
cd Music_In_Line
```

2. **Python 가상환경 생성 및 활성화**
```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 활성화 (macOS/Linux)
source venv/bin/activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

---

## 🚀 실행 방법

```bash
python app.py
```

실행 후 터미널에 표시되는 URL(기본: `http://127.0.0.1:7860`)을 브라우저에서 열어 사용합니다.

---

## 📝 사용 방법

1. **선 그리기**: 캔버스에 왼쪽에서 오른쪽 방향으로 선을 그립니다
   - 가로축 = 시간(마디), 세로축 = 음높이 (위: 높은 음, 아래: 낮은 음)
2. **선 변환하기**: `📐 선 변환하기` 버튼을 클릭하여 선을 직선 데이터로 변환합니다
   - `단순화 정도(epsilon)` 슬라이더로 단순화 정도를 조절할 수 있습니다
3. **설정 조절**: 박자(4/4, 3/4, 2/4), 마디 수(2~8), BPM(60~180)을 설정합니다
4. **음악 생성**: `🎵 음악 생성하기` 버튼을 클릭하여 MIDI 파일을 생성합니다
5. **결과 확인**: 음표 텍스트 정보를 확인하고, MIDI 파일을 다운로드합니다
6. **박자 변경**: 박자를 바꾸고 다시 `🎵 음악 생성하기`를 누르면 같은 선으로 새로운 음악이 생성됩니다

---

## 🧪 테스트 방법

```bash
python -m pytest tests/ -v
```

### 테스트 구성
- `tests/test_line_simplifier.py` — 곡선 → 직선 변환 테스트 (RDP 알고리즘, 좌→우 보정)
- `tests/test_pitch_mapper.py` — Y좌표 → MIDI pitch 매핑 테스트 (경계값, 스케일 퀀타이즈)
- `tests/test_note_arranger.py` — 음표 배열 테스트 (다양한 박자, 빈 입력)

---

## 📁 프로젝트 구조

```
Music_In_Line/
├── app.py                  # Gradio 앱 메인 진입점
├── core/
│   ├── __init__.py
│   ├── line_simplifier.py  # 곡선 → 직선 변환 (RDP 알고리즘)
│   ├── note_arranger.py    # 직선 데이터 → 음표 배열 알고리즘
│   ├── midi_generator.py   # 음표 배열 → MIDI 파일 생성
│   └── pitch_mapper.py     # Y좌표 → MIDI pitch 매핑 및 스케일 퀀타이즈
├── utils/
│   ├── __init__.py
│   └── visualization.py    # 선 변환 결과 시각화 (matplotlib)
├── output/                 # 생성된 MIDI 파일 임시 저장
├── requirements.txt
├── README.md               # 한글 가이드라인 문서
├── TODO.md                 # 향후 작업 목록
└── tests/
    ├── test_line_simplifier.py
    ├── test_note_arranger.py
    └── test_pitch_mapper.py
```

---

## ✅ 프로토타입 구현 내역

- [x] Gradio 웹 UI에서 선을 그릴 수 있다
- [x] 그린 선이 직선 데이터로 변환되고 시각화된다
- [x] 박자(4/4, 3/4, 2/4)를 선택할 수 있다
- [x] 선택한 박자에 따라 음표가 배열되고 MIDI 파일이 생성된다
- [x] 생성된 MIDI를 다운로드할 수 있다
- [x] 같은 선으로 박자만 바꿔서 새로운 음악을 생성할 수 있다
- [x] 음표 정보가 텍스트 형태로 표시된다
- [x] 단위 테스트가 통과한다
- [x] 한글 README가 작성되어 있다
- [x] TODO.md에 향후 작업 목록이 정리되어 있다

### 알려진 한계

- **MIDI 브라우저 재생**: 현재 MIDI 파일을 직접 브라우저에서 재생하는 기능은 미구현이며, 다운로드 방식으로 우회합니다.
- **악보 시각화**: `music21` 기반 악보 렌더링은 프로토타입에서 생략하였으며, 텍스트 기반 음표 정보를 제공합니다.
- **음악적 완성도**: 기초 알고리즘으로 인해 음악적으로 자연스럽지 않을 수 있습니다.

---

## 📋 향후 작업

자세한 내용은 [TODO.md](TODO.md)를 참조하세요.
