# 🔬 Music In Line — 알고리즘 연구·개발 가이드

> 이 문서는 프로토타입에서 **사용자가 직접 연구·개발하여 개선해야 할 알고리즘 영역**을 정리합니다.
> 각 항목에 대해 현재 구현 상태, 한계점, 개선 방향, 그리고 코드 수정 위치를 안내합니다.

---

## 📑 목차

1. [현재 프로토타입 파이프라인 요약](#1-현재-프로토타입-파이프라인-요약)
2. [연구·개발 항목 목록](#2-연구개발-항목-목록)
3. [항목 1: 박자 기반 직선 분할 알고리즘](#3-항목-1-박자-기반-직선-분할-알고리즘)
4. [항목 2: 음표 배열 알고리즘 (리듬 결정)](#4-항목-2-음표-배열-알고리즘-리듬-결정)
5. [항목 3: 쉼표(Rest) 생성 알고리즘](#5-항목-3-쉼표rest-생성-알고리즘)
6. [항목 4: 음높이(Pitch) 매핑 고도화](#6-항목-4-음높이pitch-매핑-고도화)
7. [항목 5: 다이나믹(강약) 표현 알고리즘](#7-항목-5-다이나믹강약-표현-알고리즘)
8. [테스트 방법 안내](#8-테스트-방법-안내)
9. [알고리즘 개발 시 주의사항](#9-알고리즘-개발-시-주의사항)

---

## 1. 현재 프로토타입 파이프라인 요약

프로토타입은 아래 5단계로 동작합니다:

```
[사용자 그림] → [좌표 추출] → [RDP 직선 단순화] → [음표 배열] → [MIDI/WAV 생성]
     ①              ②              ③                  ④              ⑤
```

| 단계 | 담당 모듈 | 현재 구현 |
|------|-----------|-----------|
| ① 사용자 그림 | `app.py` (Gradio Sketchpad) | ✅ 완성 |
| ② 좌표 추출 | `app.py` → `_extract_points_from_image()` | ✅ 완성 |
| ③ RDP 직선 단순화 | `core/line_simplifier.py` | ✅ 완성 |
| ④ 음표 배열 | `core/note_arranger.py` | ⚠️ 기초 로직만 구현 |
| ⑤ MIDI/WAV 생성 | `core/midi_generator.py`, `utils/audio_synth.py` | ✅ 완성 |

**⚠️ 마크가 있는 ④번 단계가 사용자가 직접 연구·개발해야 할 핵심 영역입니다.**

추가로, ③→④ 사이에서 **박자 설정 기반 직선 분할**이 필요하며, ④ 내부에서 **리듬·쉼표·다이나믹** 등의 음악적 요소를 고려한 알고리즘이 필요합니다.

---

## 2. 연구·개발 항목 목록

| # | 항목 | 난이도 | 수정 파일 | 현재 상태 |
|---|------|--------|-----------|-----------|
| 1 | 박자 기반 직선 분할 알고리즘 | ★★☆ | `core/note_arranger.py` | 기초 X좌표 비례 분할 |
| 2 | 음표 배열 알고리즘 (리듬 결정) | ★★★ | `core/note_arranger.py` | 가장 가까운 퀀타이즈만 사용 |
| 3 | 쉼표(Rest) 생성 알고리즘 | ★★☆ | `core/note_arranger.py`, `core/midi_generator.py` | 미구현 |
| 4 | 음높이 매핑 고도화 | ★☆☆ | `core/pitch_mapper.py` | C 메이저만 지원 |
| 5 | 다이나믹(강약) 표현 알고리즘 | ★★☆ | `core/note_arranger.py`, `core/midi_generator.py` | 미구현 |

---

## 3. 항목 1: 박자 기반 직선 분할 알고리즘

### 현재 구현

**파일**: `core/note_arranger.py` — `arrange_notes()` 함수 (192~284행)

현재 방식:
1. 캔버스 전체 폭을 마디 수로 **균등 분할** (`measure_width = canvas_width / num_measures`)
2. 각 마디 영역에 포함되는 꼭짓점을 추출 (`_get_points_in_measure()`)
3. 꼭짓점 간 X 거리를 비율로 사용하여 duration을 계산

```python
# 현재 코드 (note_arranger.py 210~211행)
beats_per_measure = time_signature[0]  # 분자가 마디당 박 수
measure_width = canvas_width / num_measures  # 마디당 캔버스 폭
```

### 한계점

- **마디 분할이 캔버스 폭 기반 균등 분할**: 선의 형태(꼭짓점 분포)와 무관하게 일정한 폭으로 나눕니다.
- **박 단위 분할 없음**: 4/4 박자에서 한 마디를 4등분(각 박)으로 분할하여 꼭짓점을 박 단위 그리드에 맞추는 과정이 없습니다.
- **꼭짓점 수와 음표 수의 관계가 불명확**: 마디 내 꼭짓점이 많을 때 어떤 기준으로 음표 수를 결정할지 명확하지 않습니다.

### 개선 방향 (연구 포인트)

1. **박 단위 그리드 스냅핑**: 각 마디를 `beats_per_measure`개의 박으로 나누고, 꼭짓점의 X좌표를 가장 가까운 박 위치에 스냅합니다.

   ```
   4/4 박자, 마디 폭 200px의 경우:
   박 그리드: [0, 50, 100, 150, 200] (4등분)

   꼭짓점 X좌표 → 스냅 결과:
   x=30  → 박 1 (0.0)
   x=65  → 박 2 (1.0)
   x=120 → 박 3 (2.0)
   ```

2. **세분 그리드(Subdivision)**: 8분음표, 16분음표 단위로 더 세밀하게 스냅할 수 있습니다.

   ```
   4/4 박자, 8분음표 단위 세분 그리드:
   [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
   ```

3. **꼭짓점 밀도 기반 음표 수 결정**: 마디 내 꼭짓점이 많으면 짧은 음표(8분·16분)를, 적으면 긴 음표(4분·2분)를 사용합니다.

### 수정 대상 코드

```python
# core/note_arranger.py

def arrange_notes(simplified_points, canvas_width, canvas_height,
                  time_signature, num_measures):
    """
    이 함수 내부의 로직을 개선해야 합니다.

    현재:
    - measure_width = canvas_width / num_measures (균등 분할)
    - 꼭짓점 간 X 거리를 비율로 사용

    개선:
    - 박 단위 그리드를 생성하고 꼭짓점을 스냅
    - 스냅된 위치를 기반으로 음표 시작/끝 결정
    """
```

### 실험용 코드 예시

아래 코드를 Python 인터프리터에서 실행하여 박 단위 스냅핑을 실험해 볼 수 있습니다:

```python
def snap_to_grid(x, measure_start_x, measure_end_x, beats_per_measure, subdivision=1):
    """
    X좌표를 박 그리드에 스냅합니다.

    Args:
        x: 원래 X좌표
        measure_start_x: 마디 시작 X좌표
        measure_end_x: 마디 끝 X좌표
        beats_per_measure: 마디당 박 수
        subdivision: 세분 단위 (1=4분음표, 2=8분음표, 4=16분음표)

    Returns:
        스냅된 박 위치 (float)
    """
    measure_width = measure_end_x - measure_start_x
    if measure_width <= 0:
        return 0.0

    # X좌표를 마디 내 비율(0~1)로 변환
    ratio = (x - measure_start_x) / measure_width

    # 박 단위로 변환
    raw_beat = ratio * beats_per_measure

    # 세분 그리드에 스냅
    grid_unit = 1.0 / subdivision
    snapped_beat = round(raw_beat / grid_unit) * grid_unit

    return max(0.0, min(beats_per_measure, snapped_beat))


# 실험
measure_start = 0
measure_end = 200
beats = 4

points_x = [15, 65, 95, 140, 185]
for x in points_x:
    snapped = snap_to_grid(x, measure_start, measure_end, beats, subdivision=2)
    print(f"x={x:3d} → 박 위치: {snapped:.1f}")
```

---

## 4. 항목 2: 음표 배열 알고리즘 (리듬 결정)

### 현재 구현

**파일**: `core/note_arranger.py` — `_quantize_duration()` 함수 (89~102행)

현재 방식:
1. 꼭짓점 간 X 거리를 정규화하여 duration 비율 산출
2. 각 duration을 가장 가까운 허용값에 퀀타이즈
3. 마디 끝에서 총 duration 보정 (`_fix_measure_duration()`)

```python
# 현재 코드 (note_arranger.py 89~102행)
def _quantize_duration(duration):
    allowed = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    return min(allowed, key=lambda d: abs(d - duration))
```

### 한계점

- **음악적 맥락 무시**: 단순히 수학적으로 가장 가까운 duration을 선택합니다.
- **박자 내 리듬 패턴 고려 없음**: 4/4 박자에서 "4분음표 + 4분음표 + 2분음표"는 자연스럽지만, "점4분음표 + 16분음표 + 2분음표"는 부자연스럽습니다.
- **강박/약박 구분 없음**: 마디의 1, 3번째 박(강박)과 2, 4번째 박(약박)에 따른 리듬 규칙이 없습니다.
- **마디 전체 음표 조합 최적화 없음**: 각 음표를 독립적으로 퀀타이즈하므로, 마디 전체적으로 보면 비정상적인 조합이 나올 수 있습니다.

### 개선 방향 (연구 포인트)

1. **리듬 패턴 템플릿 방식**: 박자별로 자주 사용되는 리듬 패턴을 미리 정의하고, 꼭짓점 수에 따라 적절한 패턴을 선택합니다.

   ```
   4/4 박자에서 음표 수별 리듬 패턴 예시:
   - 1개: [4.0]                     (온음표)
   - 2개: [2.0, 2.0]               (2분+2분)
   - 3개: [2.0, 1.0, 1.0]          (2분+4분+4분)
   - 4개: [1.0, 1.0, 1.0, 1.0]     (4분×4)
   - 5개: [1.0, 1.0, 0.5, 0.5, 1.0] (4분+4분+8분+8분+4분)
   ```

2. **동적 프로그래밍(DP) 기반 최적 조합**: 음표 duration 후보들의 조합 중, 합이 정확히 `beats_per_measure`이 되는 조합을 탐색합니다.

   ```
   목표: 합 = 4.0 (4/4 박자)
   음표 3개 필요할 때의 후보 조합:
   [2.0, 1.0, 1.0] → 합 4.0 ✓
   [1.5, 1.5, 1.0] → 합 4.0 ✓
   [1.0, 1.0, 2.0] → 합 4.0 ✓
   ...
   원래 duration 비율과 가장 유사한 조합 선택
   ```

3. **강박/약박 규칙**: 마디의 강박(1, 3박) 위치에 긴 음표를, 약박(2, 4박) 위치에 짧은 음표를 우선 배치합니다.

### 수정 대상 코드

```python
# core/note_arranger.py

# 1. _quantize_duration() 함수를 개선하거나 대체
# 2. arrange_notes() 내부에서 음표 조합 선택 로직 개선

# 현재 로직 (245~279행):
#   raw_durations → _normalize_durations() → _quantize_duration() 개별 적용
#
# 개선 방안:
#   raw_durations → _normalize_durations() → 마디 전체 최적 조합 탐색
```

### 실험용 코드 예시

```python
def find_best_rhythm(num_notes, beats_per_measure):
    """
    음표 수와 마디 박 수에 맞는 리듬 패턴을 탐색합니다.

    Args:
        num_notes: 필요한 음표 수
        beats_per_measure: 마디당 박 수

    Returns:
        duration 리스트 (합이 beats_per_measure)
    """
    allowed = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]

    # 간단한 그리디 접근: 남은 박수를 음표 수로 나누어 가장 가까운 값 선택
    durations = []
    remaining = beats_per_measure
    for i in range(num_notes):
        notes_left = num_notes - i
        target = remaining / notes_left
        chosen = min(allowed, key=lambda d: abs(d - target))
        # 남은 박수 초과 방지
        chosen = min(chosen, remaining - 0.25 * (notes_left - 1))
        chosen = max(chosen, 0.25)
        durations.append(chosen)
        remaining -= chosen

    # 보정: 합이 정확히 beats_per_measure가 되도록
    diff = beats_per_measure - sum(durations)
    if abs(diff) > 0.001:
        durations[-1] += diff

    return durations


# 실험
for n in range(1, 7):
    result = find_best_rhythm(n, 4.0)
    print(f"음표 {n}개: {result} (합: {sum(result)})")
```

---

## 5. 항목 3: 쉼표(Rest) 생성 알고리즘

### 현재 구현

**현재 프로토타입에는 쉼표 생성 기능이 없습니다.** 모든 마디가 음표로만 채워집니다.

### 한계점

- 사용자가 캔버스의 일부 영역에만 선을 그려도, 모든 마디가 빈틈없이 음표로 채워집니다.
- 음악적으로 쉼표는 리듬감을 만드는 데 매우 중요하지만, 현재는 불가능합니다.

### 개선 방향 (연구 포인트)

1. **선이 없는 영역 = 쉼표**: 마디 내에서 꼭짓점이 없는 구간을 쉼표로 처리합니다.

   ```
   마디 구간: [200, 400]
   꼭짓점: (220, y1), (280, y2)  ← 200~300 구간에만 존재

   결과:
   - 음표: 200~280 구간 → 꼭짓점 기반 음표
   - 쉼표: 280~400 구간 → 쉼표(rest)
   ```

2. **기울기 0 구간 = 쉼표**: 선이 완전히 수평인 긴 구간(기울기 ≈ 0)을 쉼표로 변환하는 방식도 가능합니다.

3. **Note 데이터 구조 확장**: 현재 `Note` 클래스에 쉼표를 나타내는 필드를 추가합니다.

### 수정 대상 코드

```python
# core/note_arranger.py — Note 클래스 확장

@dataclass
class Note:
    pitch: int         # MIDI pitch (0-127), 쉼표면 사용 안 함
    start_beat: float  # 마디 내 시작 위치 (박 단위)
    duration: float    # 음표/쉼표 길이 (박 단위)
    measure: int       # 소속 마디 번호 (0부터 시작)
    is_rest: bool = False  # ← 추가: True이면 쉼표
```

```python
# core/midi_generator.py — 쉼표 처리

# 현재 모든 Note를 midi.addNote()로 추가하고 있는데,
# is_rest=True인 음표는 건너뛰면 됩니다.
for note in notes:
    if hasattr(note, 'is_rest') and note.is_rest:
        continue  # 쉼표는 MIDI에 추가하지 않음
    midi.addNote(...)
```

### 실험용 코드 예시

```python
def detect_rest_regions(measure_points, measure_start_x, measure_end_x,
                        beats_per_measure, min_rest_ratio=0.2):
    """
    마디 내에서 쉼표가 필요한 영역을 감지합니다.

    Args:
        measure_points: 마디 내 꼭짓점 리스트
        measure_start_x: 마디 시작 X좌표
        measure_end_x: 마디 끝 X좌표
        beats_per_measure: 마디당 박 수
        min_rest_ratio: 쉼표로 처리할 최소 빈 구간 비율

    Returns:
        쉼표 영역 리스트 [(start_beat, duration), ...]
    """
    measure_width = measure_end_x - measure_start_x
    if measure_width <= 0 or not measure_points:
        return [(0.0, float(beats_per_measure))]  # 마디 전체가 쉼표

    rests = []

    # 마디 시작부터 첫 꼭짓점까지의 빈 구간
    first_x = measure_points[0][0]
    if first_x > measure_start_x:
        gap_ratio = (first_x - measure_start_x) / measure_width
        if gap_ratio >= min_rest_ratio:
            rest_dur = gap_ratio * beats_per_measure
            rests.append((0.0, rest_dur))

    # 마지막 꼭짓점부터 마디 끝까지의 빈 구간
    last_x = measure_points[-1][0]
    if last_x < measure_end_x:
        gap_ratio = (measure_end_x - last_x) / measure_width
        if gap_ratio >= min_rest_ratio:
            rest_start = (last_x - measure_start_x) / measure_width * beats_per_measure
            rest_dur = gap_ratio * beats_per_measure
            rests.append((rest_start, rest_dur))

    return rests


# 실험
rests = detect_rest_regions(
    measure_points=[(220, 100), (280, 200)],
    measure_start_x=200,
    measure_end_x=400,
    beats_per_measure=4
)
print(f"쉼표 영역: {rests}")
# 예상 출력: [(2.0, 2.4)] — 마디 끝 부분에 쉼표
```

---

## 6. 항목 4: 음높이(Pitch) 매핑 고도화

### 현재 구현

**파일**: `core/pitch_mapper.py`

현재 방식:
- Y좌표를 선형으로 MIDI pitch 범위(60~84, C4~C6)에 매핑
- C 메이저 스케일(흰 건반)에만 퀀타이즈

```python
# 현재 코드 (pitch_mapper.py 9행)
C_MAJOR_OFFSETS = [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B
```

### 한계점

- **C 메이저만 지원**: D 마이너, G 믹솔리디안 등 다른 스케일을 사용할 수 없습니다.
- **음역 고정**: pitch 범위가 60~84(C4~C6)로 고정되어 있습니다.
- **펜타토닉 스케일 미지원**: 초등학생 교육에 자주 사용되는 5음 스케일이 없습니다.

### 개선 방향 (연구 포인트)

1. **다양한 스케일 지원**: 스케일별 오프셋 테이블을 추가합니다.

   ```python
   # 각 값은 C(=0)부터의 반음(semitone) 간격입니다.
   SCALES = {
       "C_major":      [0, 2, 4, 5, 7, 9, 11],    # C, D, E, F, G, A, B
       "C_minor":      [0, 2, 3, 5, 7, 8, 10],    # C, D, Eb, F, G, Ab, Bb
       "C_pentatonic": [0, 2, 4, 7, 9],            # C, D, E, G, A (5음 스케일, 교육용)
       "C_blues":      [0, 3, 5, 6, 7, 10],        # C, Eb, F, F#, G, Bb
       "G_major":      [0, 2, 4, 5, 7, 9, 11],    # 오프셋은 동일, root_note=7(G)로 전조
       # G 메이저 사용 시: 각 pitch에 root_note를 더하여 매핑
   }
   ```

2. **음역(Pitch Range) 설정 UI**: 사용자가 최저/최고 음을 선택할 수 있도록 합니다.

3. **조(Key) 변경**: 기본 C 메이저에서 다른 조로 전조(transpose)할 수 있는 기능을 추가합니다.

### 수정 대상 코드

```python
# core/pitch_mapper.py

# _get_scale_pitches() 함수 내 스케일 분기 로직을 확장
def _get_scale_pitches(pitch_min, pitch_max, scale="C_major"):
    # 현재: scale != "C_major"이면 ValueError
    # 개선: SCALES 딕셔너리에서 오프셋을 가져와 사용
    ...
```

---

## 7. 항목 5: 다이나믹(강약) 표현 알고리즘

### 현재 구현

**파일**: `core/midi_generator.py` (35행)

현재 방식: 모든 음표의 MIDI velocity(음량)가 100으로 고정되어 있습니다.

```python
volume = 100  # 음량 (0~127)
```

### 한계점

- 모든 음표가 같은 세기로 재생되어 단조롭게 들립니다.
- 선의 특성(기울기, 속도 등)이 강약에 반영되지 않습니다.

### 개선 방향 (연구 포인트)

1. **기울기 크기 → 음량**: 선의 기울기가 급할수록(변화가 클수록) 큰 소리, 완만할수록 작은 소리로 매핑합니다.

   ```
   기울기 절대값 → MIDI velocity 매핑:
   |slope| ≈ 0   → velocity 60  (piano, 여리게)
   |slope| ≈ 1   → velocity 90  (mezzo-forte, 보통)
   |slope| ≈ 3+  → velocity 120 (forte, 세게)
   ```

2. **강박/약박에 따른 악센트**: 마디 시작(강박)의 음표를 약간 더 크게, 약박의 음표를 약간 작게 합니다.

   ```
   4/4 박자 기본 악센트:
   박 1: velocity + 10 (강박)
   박 2: velocity - 5 (약박)
   박 3: velocity + 5 (중간 강박)
   박 4: velocity - 5 (약박)
   ```

3. **Note 데이터 구조 확장**: velocity 필드를 추가합니다.

### 수정 대상 코드

```python
# core/note_arranger.py — Note 클래스에 velocity 추가

@dataclass
class Note:
    pitch: int
    start_beat: float
    duration: float
    measure: int
    velocity: int = 100  # ← 추가: MIDI velocity (0~127)

# core/midi_generator.py — velocity 적용
midi.addNote(
    ...
    volume=note.velocity if hasattr(note, 'velocity') else volume,
)
```

---

## 8. 테스트 방법 안내

### 8-1. 기존 테스트 실행

알고리즘을 수정한 후 반드시 기존 테스트가 통과하는지 확인하세요:

```powershell
python -m pytest tests/ -v
```

32개 테스트가 모두 `PASSED`로 나와야 합니다.

### 8-2. 새로운 테스트 추가

알고리즘을 개선할 때, 해당 기능에 대한 테스트도 함께 추가하는 것을 권장합니다.

**테스트 파일 위치**: `tests/test_note_arranger.py`

**테스트 추가 예시**:

```python
# tests/test_note_arranger.py에 추가

def test_rhythm_pattern_fits_measure(self):
    """마디 내 음표의 duration 합이 정확히 beats_per_measure인지 확인"""
    points = [(0, 100), (100, 300), (200, 50), (400, 250),
              (500, 350), (600, 100), (700, 200), (800, 300)]
    for ts_name, ts in [("4/4", (4, 4)), ("3/4", (3, 4)), ("2/4", (2, 4))]:
        result = arrange_notes(points, 800, 400, ts, 4)
        for m in range(4):
            measure_notes = [n for n in result if n.measure == m]
            total = sum(n.duration for n in measure_notes)
            assert total == pytest.approx(ts[0], abs=0.01), \
                f"{ts_name} 마디 {m}: 총 {total}박 (기대: {ts[0]}박)"

def test_rest_generation(self):
    """쉼표가 올바르게 생성되는지 확인 (쉼표 기능 추가 후)"""
    # 캔버스 왼쪽 절반에만 선을 그린 경우
    points = [(0, 100), (200, 300), (400, 150)]
    result = arrange_notes(points, 800, 400, (4, 4), 4)
    # 오른쪽 절반의 마디에 쉼표가 포함되는지 확인
    # (쉼표 기능 구현 후 이 테스트를 활성화하세요)
    pass
```

### 8-3. 스트레스 테스트 (랜덤 입력)

MIDI 생성 오류를 방지하기 위해, 다양한 입력에 대한 스트레스 테스트를 실행하세요:

```python
import random
from core.note_arranger import arrange_notes
from core.midi_generator import generate_midi
import tempfile, os

random.seed(42)
errors = 0

for trial in range(100):
    num_points = random.randint(2, 20)
    points = sorted(
        [(random.uniform(0, 800), random.uniform(0, 400))
         for _ in range(num_points)],
        key=lambda p: p[0]
    )

    for ts in [(4, 4), (3, 4), (2, 4)]:
        for nm in [2, 4, 6, 8]:
            try:
                notes = arrange_notes(points, 800, 400, ts, nm)
                if notes:
                    fd, path = tempfile.mkstemp(suffix='.mid')
                    os.close(fd)
                    generate_midi(notes, bpm=120, time_signature=ts, output_path=path)
                    os.unlink(path)
            except Exception as e:
                errors += 1
                print(f"Trial {trial}, ts={ts}, nm={nm}: {e}")

print(f"\n결과: {errors}개 오류 발생")
```

---

## 9. 알고리즘 개발 시 주의사항

### 9-1. 반드시 지켜야 할 규칙

| 규칙 | 이유 |
|------|------|
| 마디 내 음표 duration 합 = `beats_per_measure` | 합이 다르면 리듬이 틀어지고 MIDI 재생 시 문제 발생 |
| 음표 duration > 0 | 0 또는 음수 duration은 MIDI 라이브러리 오류 발생 |
| 같은 절대 시간에 같은 pitch 중복 불가 | `midiutil`의 `deInterleaveNotes` 오류 발생 (IndexError) |
| MIDI pitch 범위: 0~127 | MIDI 표준 범위 |
| start_beat 범위: 0 ≤ start_beat < beats_per_measure | 마디 경계를 넘으면 재생 위치가 틀어짐 |

### 9-2. 데이터 흐름 (수정 시 참고)

```
사용자 그림 (캔버스)
    ↓
[app.py] _extract_points_from_sketchpad()
    ↓
원시 좌표: [(x1,y1), (x2,y2), ...]
    ↓
[app.py] enforce_left_to_right() → simplify_line()
    ↓
단순화된 꼭짓점: [(x1,y1), (x2,y2), ...]  ← 이것이 arrange_notes()의 입력
    ↓
[core/note_arranger.py] arrange_notes()      ← ★ 주요 수정 대상
    ↓
Note 리스트: [Note(pitch, start_beat, duration, measure), ...]
    ↓
[core/midi_generator.py] generate_midi()     ← MIDI 생성 (중복 방지 로직 포함)
[utils/audio_synth.py] synthesize_wav()      ← WAV 합성
```

### 9-3. 디버깅 팁

알고리즘을 수정할 때 아래 방법으로 중간 결과를 확인할 수 있습니다:

```python
from core.line_simplifier import simplify_line
from core.note_arranger import arrange_notes, notes_to_text

# 샘플 데이터
points = [(0, 100), (100, 300), (200, 50), (400, 200), (600, 350), (800, 150)]
simplified = simplify_line(points, epsilon=5.0)

print(f"단순화된 꼭짓점 ({len(simplified)}개):")
for i, (x, y) in enumerate(simplified):
    print(f"  [{i}] x={x:.1f}, y={y:.1f}")

# 박자별 결과 비교
for ts_name, ts in [("4/4", (4, 4)), ("3/4", (3, 4)), ("2/4", (2, 4))]:
    notes = arrange_notes(simplified, 800, 400, ts, 4)
    print(f"\n{'='*50}")
    print(f"박자: {ts_name}, 음표 수: {len(notes)}")
    print(f"{'='*50}")
    for n in notes:
        print(f"  마디 {n.measure}: pitch={n.pitch}, "
              f"시작={n.start_beat:.2f}박, 길이={n.duration:.2f}박")
    print(notes_to_text(notes))
```

### 9-4. 함수 시그니처 유지

`arrange_notes()` 함수의 **입력/출력 인터페이스를 변경하지 마세요**. `app.py`에서 이 함수를 호출하고 있으므로, 시그니처가 바뀌면 앱이 동작하지 않습니다.

```python
# 이 시그니처를 유지해야 합니다:
def arrange_notes(simplified_points, canvas_width, canvas_height,
                  time_signature, num_measures) -> list[Note]:
    ...
```

`Note` 클래스에 새 필드(예: `velocity`, `is_rest`)를 추가할 때는 반드시 **기본값**을 지정하여 기존 코드와의 호환성을 유지하세요.

```python
@dataclass
class Note:
    pitch: int
    start_beat: float
    duration: float
    measure: int
    velocity: int = 100   # 기본값 → 기존 코드 영향 없음
    is_rest: bool = False  # 기본값 → 기존 코드 영향 없음
```

---

## 📌 요약: 개발 우선순위 제안

| 순위 | 항목 | 이유 |
|------|------|------|
| 1 | 음표 배열 알고리즘 (리듬 결정) | 음악적 품질에 가장 큰 영향 |
| 2 | 박자 기반 직선 분할 알고리즘 | 리듬 결정의 기초가 되는 그리드 시스템 |
| 3 | 쉼표 생성 알고리즘 | 음악적 자연스러움에 필수 |
| 4 | 다이나믹(강약) 표현 | 음악적 표현력 향상 |
| 5 | 음높이 매핑 고도화 | 다양한 스케일/조 지원으로 활용도 확대 |

> 💡 **권장 접근**: 항목 2(박자 기반 분할) → 항목 1(리듬 결정) 순서로 개발하면 서로 연결되어 효과적입니다. 이 두 가지를 먼저 완성한 후, 항목 3(쉼표)을 추가하세요.
