"""Streamlit screen: 무엇이 필요한지 → 왜 필요한지 → 무엇을 공부할지, with the evidence behind each step."""
import json
from pathlib import Path

import streamlit as st

from skillpath.recommend import recommend
from skillpath.sections import SECTION_LABELS
from skillpath.skills import ROOT, SkillDictionary

DATASETS = {'실제 공고 (Techmap)': ROOT / 'outputs' / 'real', '합성 예시': ROOT / 'outputs' / 'latest'}
STATUS_LABELS = {'confirmed': '확인', 'uncertain': '불확실', 'rejected': '제외'}
REQUIREMENT_LABELS = {'required': '필수', 'preferred': '우대', 'responsibility': '업무', 'unknown': '구분 없음'}
BODY_LABELS = {'has_sections': '자격요건·우대사항 구분됨', 'no_sections': '본문은 있으나 구분 없음', 'no_body': '본문 없음(이미지 등)'}
REASON_LABELS = {'evidence_not_in_source': '근거 문장이 원문에 없음', 'skill_not_in_dictionary': '사전에 없는 기술명',
                 'skill_not_in_evidence': '근거 문장에 해당 기술이 없음', 'requirement_conflict': '필수/우대 판정이 원문과 다름',
                 'unknown_section': '알 수 없는 섹션', 'unknown_posting': '알 수 없는 공고'}


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


st.set_page_config(page_title='채용공고 기반 학습경로', layout='wide')
available = {name: path for name, path in DATASETS.items() if (path / 'run.json').exists()}
if not available:
    st.error('분석 결과가 없습니다. 먼저 `python -m skillpath.pipeline`을 실행하세요.')
    st.stop()
with st.sidebar:
    OUT = available[st.radio('데이터', list(available))]

run, postings, courses = read('run.json'), read('postings.json'), read('courses.json')
claims, rows = read('claims.json'), read('demand.json')
skills = SkillDictionary.load()
by_posting = {p['id']: p for p in postings}

st.title('채용공고 기반 학습경로 추천')
if run.get('jobs_synthetic', run['synthetic']):
    st.warning('합성 공고로 흐름만 검증한 결과입니다. 실제 채용시장 분석 결과가 아닙니다.')
else:
    sources = ', '.join(f'{k} {v}' for k, v in run.get('sources', {}).items())
    st.info(f"수집된 국내 공고 {run['postings']}건 기준 (Techmap API, 원 출처: {sources}). "
            '대한민국 전체 채용시장의 대표값이 아닙니다.')
if run.get('courses_synthetic'):
    st.warning('교육과정은 아직 합성 데이터입니다. 추천 과정은 흐름 확인용입니다.')
st.caption(f"공고 {run['postings']}건 · 교육 {run['courses_n']}개 · 추출기 {run['extractor']}"
           f"{' (' + run['model'] + ')' if run.get('model') else ''} · 실행 {run['run_at']}")

roles = sorted({p['role'] for p in postings})
with st.sidebar:
    role = st.selectbox('목표 직무', roles)
    have = st.multiselect('보유 기술', skills.names())
    extra = st.text_input('사전에 없는 기술 (쉼표로 구분)')
user_skills = have + [s.strip() for s in extra.split(',') if s.strip()]

role_rows = [r for r in rows if r['role'] == role and r['mention_n'] > 0]
result = recommend(role, user_skills, rows, courses, skills)
gap_items = {item['gap']['skill']: item for item in result['items']}

st.header(f'1. {role} 공고가 요구하는 기술')
base = role_rows[0] if role_rows else {'postings': 0, 'excluded_postings': 0}
excluded = f" (본문이 이미지라 제외 {base['excluded_postings']}건)" if base['excluded_postings'] else ''
st.caption(f"{role} 공고 중 본문을 읽을 수 있는 {base['postings']}건 기준{excluded}. "
           '필수 → 언급 비율 순. 모든 숫자는 코드가 원문에서 확인한 근거만으로 계산합니다. '
           '"구분 없음"은 필수/우대를 원문에서 판단할 수 없는 언급입니다.')
st.dataframe([{'기술': r['skill'], '필수': r['required_n'], '우대': r['preferred_n'],
               '업무': r['responsibility_n'], '구분 없음': r['unknown_n'],
               '언급 공고': r['mention_n'], '언급 비율': f"{r['mention_share']:.0%}", '불확실': r['uncertain_n'],
               '내 상태': '부족' if r['skill'] in gap_items else '보유',
               '확인된 과정': (', '.join(p['course']['title'] for p in gap_items[r['skill']]['courses']) or '없음')
                             if r['skill'] in gap_items else '-'}
              for r in role_rows], hide_index=True, use_container_width=True)
picked = st.selectbox('근거 문장 보기', [r['skill'] for r in role_rows]) if role_rows else None
for r in role_rows:
    if r['skill'] != picked:
        continue
    for e in r['evidence']:
        p = by_posting[e['posting_id']]
        req = REQUIREMENT_LABELS[e['requirement']]
        link = f" · [원문]({p['url']})" if p.get('url') else ''
        source = f" · {p['source']}" if p.get('source') else ''
        st.markdown(f"- **{p['company']} · {p['title']}** ({SECTION_LABELS[e['section']]}, {req}{source}{link}): “{e['quote']}”")

st.header('2. 나에게 부족한 기술과 추천 교육')
if result['unrecognized_inputs']:
    st.info(f"사전에 없어 비교하지 못한 입력: {', '.join(result['unrecognized_inputs'])}")
with_course = [i for i in result['items'] if i['courses']]
without_course = [i for i in result['items'] if not i['courses']]
if not result['items']:
    st.success('이 직무에서 확인된 요구 기술을 모두 보유했다고 입력했습니다.')
else:
    st.caption(f"부족 기술 {len(result['items'])}개 · 과정 확인 {len(with_course)}개 · "
               f"확인된 과정 없음 {len(without_course)}개 (1번 표와 같은 순서)")
for item in with_course:
    gap = item['gap']
    st.subheader(f"{gap['skill']} — 필수 {gap['required_n']}건 · 우대 {gap['preferred_n']}건")
    st.write(item['reason'])
    for pick in item['courses']:
        c = pick['course']
        line = f"**{c['title']}** ({c['provider']}) · 난이도 {pick['level']} · 선수지식 {pick['prerequisites']}"
        if pick['missing_prerequisites']:
            line += f" · 먼저 필요한 기술: {', '.join(pick['missing_prerequisites'])}"
        st.markdown(f"- {line}" + (f" · [링크]({c['url']})" if c.get('url') else ''))
if without_course:
    st.subheader('확인된 과정이 없는 부족 기술')
    st.caption('교육 데이터의 과정명·소개·커리큘럼에서 이 기술을 찾지 못해 추천하지 않았습니다.')
    st.dataframe([{'기술': i['gap']['skill'], '필수': i['gap']['required_n'], '우대': i['gap']['preferred_n'],
                   '언급 공고': i['gap']['mention_n']}
                  for i in without_course], hide_index=True, use_container_width=True)

st.header('3. 검증 현황')
status = run['status']
cols = st.columns(3)
for col, key in zip(cols, ('confirmed', 'uncertain', 'rejected')):
    col.metric(STATUS_LABELS[key], status.get(key, 0))
queue = [c for c in claims if c['status'] != 'confirmed']
if queue:
    st.dataframe([{'공고': c['posting_id'], '기술': c['skill'], '상태': STATUS_LABELS[c['status']],
                   '사유': ', '.join(REASON_LABELS.get(r, r) for r in c['reasons']), '근거': c['evidence']}
                  for c in queue], hide_index=True, use_container_width=True)
else:
    st.caption('불확실하거나 제외된 추출 결과가 없습니다.')
if run.get('body_status'):
    st.caption('공고 본문 상태: ' + ', '.join(f'{BODY_LABELS.get(k, k)} {v}건' for k, v in run['body_status'].items()))
if run.get('dictionary_gaps'):
    st.subheader('사전이 보지 못하는 기술 후보')
    st.caption('데이터 제공자가 붙인 태그 중 우리 사전이 표준명으로 바꾸지 못한 것입니다. 근거가 아니라 사전 보강 후보이며, '
               '사람이 확인한 뒤 사전에 추가합니다. 성향 같은 비기술 태그도 섞여 있습니다.')
    st.dataframe([{'태그': g['skill'], '공고 수': g['postings']} for g in run['dictionary_gaps']],
                 hide_index=True, use_container_width=True)
