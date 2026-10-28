'use strict';

(() => {
  const $ = id => document.getElementById(id);
  const PAGE_SIZE = 24;
  let snapshot = null;
  let entries = [];
  let visibleCount = PAGE_SIZE;
  let filtered = [];
  let searchTimer;
  let dialogTrigger = null;
  const numeric = v => typeof v === 'number' && Number.isFinite(v);
  const object = v => v && typeof v === 'object' && !Array.isArray(v) ? v : {};
  const array = v => Array.isArray(v) ? v : [];
  const count = v => Object.keys(object(v)).length;
  const nfmt = n => Number(n).toLocaleString('zh-CN');
  const number = (n, digits = 2) => numeric(n) ? n.toFixed(digits) : '—';
  const text = v => v == null ? '' : String(v);
  const metric = (skill, key) => object(skill[key]);
  const metricKeys = (skill, key) => Object.keys(metric(skill, key)).filter(m => numeric(metric(skill, key)[m]));
  function node(tag, className, content) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content != null) element.textContent = text(content);
    return element;
  }
  function append(parent, ...children) {
    children.filter(Boolean).forEach(child => parent.append(child));
    return parent;
  }
  function status(label, type = '') { return node('span', `status-pill ${type}`, label); }
  function pairedModels(skill) {
    return metricKeys(skill, 'm2_mean').filter(m => numeric(metric(skill, 'm1_mean')[m]) && numeric(metric(skill, 'm4_mean')[m]));
  }
  function mean(values) {
    const numbers = values.filter(numeric);
    return numbers.length ? numbers.reduce((a, b) => a + b, 0) / numbers.length : null;
  }
  function selectedModel() { return $('model-filter').value; }
  function scoreFor(skill, model = selectedModel()) {
    return model ? metric(skill, 'm2_mean')[model] : mean(Object.values(metric(skill, 'm2_mean')));
  }
  function pairedFor(skill, model = selectedModel()) {
    const models = pairedModels(skill);
    return model ? models.includes(model) : models.length > 0;
  }
  function nameFor(entry) { return text(entry.data.skill || entry.id); }
  function functionFor(skill) { return text(skill['功能'] || skill.description || '快照未提供功能释义'); }
  function scoreElement(value, small = '') {
    const wrap = node('span', 'score-cell');
    append(wrap, node('strong', numeric(value) ? '' : 'no-data', number(value)), small ? node('small', '', small) : null);
    return wrap;
  }
  function makeOpenButton(entry, className = 'skill-open', label = nameFor(entry)) {
    const button = node('button', className, label);
    button.type = 'button';
    button.addEventListener('click', () => openDetail(entry, button));
    return button;
  }
  function setStat(label, value, note, highlight) {
    const card = node('article', `stat-card ${highlight ? 'highlight' : ''}`);
    append(card, node('span', '', label), node('strong', '', numeric(value) ? nfmt(value) : text(value)), node('small', '', note));
    return card;
  }

  function renderSnapshot() {
    const modelNames = [...new Set(entries.flatMap(e => metricKeys(e.data, 'm2_mean')))];
    const totalM2 = entries.reduce((acc, e) => acc + metricKeys(e.data, 'm2_mean').length, 0);
    const paired = entries.filter(e => pairedModels(e.data).length > 0).length;
    $('stats').replaceChildren(
      setStat('技能条目', entries.length, '当前快照收录'),
      setStat('模型别名', modelNames.length, '原始通道标识，非已固定版本'),
      setStat('M2 配对记录', totalM2, '技能 × 模型，有绝对均分'),
      setStat('有三模式对照', paired, '同一模型含 M1 / M2 / M4', true)
    );
    $('snapshot-time').textContent = `快照生成于 ${text(snapshot.generated || '未提供时间')}`;
    $('snapshot-note').textContent = `从当前 data.json 计算 · ${nfmt(entries.length - paired)} 个条目缺少同模型的完整三模式对照 · 快照时间不代表评测完成时间。`;
    const previousModel = selectedModel();
    $('model-filter').replaceChildren(node('option', '', '全部模型'));
    $('model-filter').firstChild.value = '';
    modelNames.sort((a, b) => a.localeCompare(b)).forEach(m => {
      const option = node('option', '', m);
      option.value = m;
      $('model-filter').append(option);
    });
    if (modelNames.includes(previousModel)) $('model-filter').value = previousModel;
    renderCoverage();
    renderGroups();
    renderOperations();
  }

  function renderCoverage() {
    const kinds = [
      ['M2 带技能', 'm2_mean', false],
      ['M1 裸跑', 'm1_mean', true],
      ['M4 对照', 'm4_mean', true],
      ['M3 触发记录', 'trigger_accuracy', true]
    ];
    $('coverage-bars').replaceChildren(...kinds.map(([label, key, control]) => {
      const covered = entries.filter(e => count(e.data[key]) > 0).length;
      const percent = entries.length ? covered / entries.length * 100 : 0;
      const row = node('div', `coverage-row ${control ? 'control' : ''}`);
      const bar = node('div', 'bar');
      const fill = node('span');
      fill.style.width = `${percent}%`;
      bar.append(fill);
      bar.setAttribute('aria-hidden', 'true');
      append(row, node('span', '', label), bar, node('strong', '', `${nfmt(covered)} / ${nfmt(entries.length)}`));
      row.title = `${label} 覆盖 ${number(percent, 2)}%`;
      return row;
    }));
  }

  function filterEntries(reset = true) {
    if (!snapshot) return;
    if (reset) visibleCount = PAGE_SIZE;
    const q = $('search').value.trim().toLocaleLowerCase();
    const model = selectedModel();
    const sort = $('sort').value;
    filtered = entries.filter(entry => {
      const skill = entry.data;
      if (q && !`${nameFor(entry)} ${functionFor(skill)}`.toLocaleLowerCase().includes(q)) return false;
      if (model && !numeric(metric(skill, 'm2_mean')[model])) return false;
      if ($('paired-only').checked && !pairedFor(skill, model)) return false;
      return true;
    });
    filtered.sort((a, b) => {
      let delta = 0;
      if (sort === 'evidence') delta = Number(pairedFor(b.data, model)) - Number(pairedFor(a.data, model));
      if (sort === 'score') delta = (scoreFor(b.data, model) ?? -1) - (scoreFor(a.data, model) ?? -1);
      if (sort === 'models') delta = metricKeys(b.data, 'm2_mean').length - metricKeys(a.data, 'm2_mean').length;
      return (Number.isFinite(delta) && delta !== 0 ? delta : 0) || nameFor(a).localeCompare(nameFor(b), 'zh-CN');
    });
    renderSkills();
  }

  function renderSkills() {
    const shown = filtered.slice(0, visibleCount);
    const fragment = document.createDocumentFragment();
    shown.forEach((entry, i) => {
      const skill = entry.data;
      const row = node('tr');
      const titleCell = node('td');
      const description = node('span', 'skill-function', functionFor(skill));
      description.title = functionFor(skill);
      append(titleCell, makeOpenButton(entry), description);
      const score = node('td', 'score-cell');
      score.append(scoreElement(scoreFor(skill), '/ 5'));
      const models = metricKeys(skill, 'm2_mean').length;
      const evidence = node('td');
      evidence.append(status(pairedFor(skill) ? '有历史对照 · 待核验' : (metricKeys(skill, 'm2_mean').length ? '证据不足 · M2 快扫' : '尚无 M2 评分'), pairedFor(skill) ? 'paired' : ''));
      const action = node('td');
      const actionButton = makeOpenButton(entry, 'inspect-button', '↗');
      actionButton.setAttribute('aria-label', `查看 ${nameFor(entry)} 的模型配对详情`);
      action.append(actionButton);
      append(row, node('td', 'rank-cell', String(i + 1).padStart(2, '0')), titleCell, score, node('td', '', `${models} 个模型`), evidence, action);
      fragment.append(row);
    });
    $('skills-body').replaceChildren(fragment);
    const result = node('strong', '', nfmt(filtered.length));
    $('result-count').replaceChildren('找到 ', result, ` 个技能${selectedModel() ? ` · ${selectedModel()}` : ' · M2 展示模型均值'} `);
    $('no-results').hidden = filtered.length > 0;
    $('pagination').hidden = filtered.length === 0;
    $('page-status').textContent = `已显示 ${nfmt(shown.length)} / ${nfmt(filtered.length)} 个技能`;
    $('load-more').hidden = shown.length >= filtered.length;
    const scoreHeading = document.querySelector('.skills-table th:nth-child(3)');
    scoreHeading.textContent = selectedModel() ? '模型 M2 均分' : '跨模型 M2 均分';
  }

  function renderGroups() {
    const previous = $('group-filter').value;
    const groups = array(snapshot.cross).filter(g => array(g.skills).length > 0);
    $('group-filter').replaceChildren();
    groups.forEach((group, index) => {
      const option = node('option', '', `${text(group['组'] || `功能组 ${index + 1}`)} · ${array(group.skills).length} 项`);
      option.value = String(index);
      $('group-filter').append(option);
    });
    if (!groups.length) {
      const option = node('option', '', '快照没有功能组'); option.value = '';
      $('group-filter').append(option);
    } else if (previous !== '' && Number(previous) < groups.length) $('group-filter').value = previous;
    $('group-filter')._groups = groups;
    renderGroup();
  }

  function renderGroup() {
    const groups = $('group-filter')._groups || [];
    const group = groups[Number($('group-filter').value)];
    $('group-grid').replaceChildren();
    if (!group) {
      $('group-grid').append(node('p', 'muted', '快照未提供同类分组。'));
      return;
    }
    const ids = array(group.skills);
    ids.slice(0, 6).forEach((id, index) => {
      const entry = entries.find(e => e.id === id);
      const card = node('article', 'group-card');
      append(card, node('span', 'group-index', `RELATED SKILL / ${String(index + 1).padStart(2, '0')}`));
      if (!entry) {
        append(card, node('h3', '', id), node('p', 'group-function', '分组中存在此条目，当前技能快照未提供明细。'));
      } else {
        const heading = node('h3'); heading.append(makeOpenButton(entry));
        append(card, heading, node('p', 'group-function', functionFor(entry.data)), status(pairedModels(entry.data).length ? '有历史对照 · 待核验' : '增益证据不足', pairedModels(entry.data).length ? 'paired' : ''));
        const footer = node('div', 'group-card-footer');
        const score = node('span', 'group-score');
        append(score, node('small', '', '跨模型 M2 绝对均分'), number(scoreFor(entry.data, '')));
        const button = makeOpenButton(entry, 'inspect-button', '↗');
        button.setAttribute('aria-label', `查看 ${nameFor(entry)} 的详情`);
        append(footer, score, button); card.append(footer);
      }
      $('group-grid').append(card);
    });
    if (ids.length > 6) $('group-grid').append(node('p', 'group-more', `展示该组前 6 项，共 ${nfmt(ids.length)} 项。完整分组见可下载的原始快照。`));
  }

  function renderOperations() {
    const live = object(snapshot.live);
    const progress = array(live.progress || snapshot.progress);
    const generated = text(snapshot.generated || '未提供');
    const lines = [
      ['快照生成时间', generated],
      ['台账快照时间', text(live.generated || '未提供')],
      ['快照中的进度项', `${nfmt(progress.length)} 项`],
      ['实时运行状态', '静态文件无法确认']
    ];
    $('run-metadata').replaceChildren(...lines.map(([label, value]) => append(node('div', 'metadata-line'), node('span', '', label), node('strong', '', value))), node('p', '', '展示的是文件中保存的状态；空进度不等于已完成，历史成功记录也不代表管线此刻正在运行。'));
    const records = array(live.recent).slice(0, 5);
    $('recent-records').replaceChildren(...records.map(record => {
      const row = node('div', 'recent-record');
      const state = text(record['状态'] || '未提供');
      const detail = `${text(record['技能'] || '未命名技能')} · ${text(record['模型'] || '未知模型')}`;
      const name = node('span', 'recent-name', detail); name.title = detail;
      append(row, node('time', '', record['时间'] || '—'), name, node('span', `recent-state ${state !== 'ok' ? 'failed' : ''}`, state === 'ok' ? '记录成功' : state));
      return row;
    }));
    if (!records.length) $('recent-records').append(node('p', 'muted', '快照未提供近期台账。'));
  }

  function detailSection(title, description) {
    const section = node('section', 'detail-section');
    append(section, node('h3', '', title), description ? node('p', '', description) : null);
    return section;
  }
  function table(headers, rows, className = '') {
    const scroll = node('div', 'table-scroll');
    scroll.tabIndex = 0;
    scroll.setAttribute('role', 'region');
    scroll.setAttribute('aria-label', headers.join('、'));
    const element = node('table', `detail-table ${className}`);
    const head = node('thead'); const hr = node('tr');
    headers.forEach(label => { const th = node('th', '', label); th.scope = 'col'; hr.append(th); });
    head.append(hr); element.append(head);
    const body = node('tbody');
    rows.forEach(values => {
      const row = node('tr');
      values.forEach(value => {
        const td = node('td');
        if (value instanceof Node) td.append(value); else td.textContent = text(value);
        row.append(td);
      });
      body.append(row);
    });
    element.append(body); scroll.append(element); return scroll;
  }

  function openDetail(entry, trigger) {
    dialogTrigger = trigger;
    const skill = entry.data;
    const content = $('detail-content');
    const title = node('h2', 'detail-title', nameFor(entry)); title.id = 'detail-title';
    const pair = pairedModels(skill);
    const meta = append(node('div', 'detail-meta'), status(pair.length ? '有历史对照 · 待核验' : '增益证据不足', pair.length ? 'paired' : ''), node('span', '', `条目聚合时间：${text(skill.generated || '未提供')}`));
    content.replaceChildren(title, node('p', 'detail-description', functionFor(skill)), meta, node('p', 'detail-notice', '以下展示历史绝对评分。M1、M2、M4 曾采用不同评分权重，不能直接相减解释技能净增益。当前快照也未完整固定模型、任务与执行环境版本；结论需要重新配对验证。'));
    const models = [...new Set(['m1_mean', 'm2_mean', 'm4_mean', 'skill_score', 'trigger_accuracy'].flatMap(key => Object.keys(metric(skill, key))))].sort();
    const means = detailSection('模型配对记录', '分数范围 0–5；SkillScore 范围 0–100。缺失字段显示 —，不补分，不推断。');
    if (models.length) {
      means.append(table(['模型 / 原始别名', 'M2 均分', 'M1 均分', 'M4 均分', '历史 SkillScore', '触发记录'], models.map(m => [m, node('span', 'accent-text', number(metric(skill, 'm2_mean')[m])), number(metric(skill, 'm1_mean')[m]), number(metric(skill, 'm4_mean')[m]), number(metric(skill, 'skill_score')[m], 1), text(metric(skill, 'trigger_accuracy')[m] || '—')])));
    } else means.append(node('p', 'muted', '此技能尚无模型均分记录。'));
    content.append(means);
    const matrix = object(skill.judge_matrix_M2);
    const producers = Object.keys(matrix);
    const judges = [...new Set(producers.flatMap(p => Object.keys(object(matrix[p]))))].sort();
    const matrixSection = detailSection('M2 生产者 × 判官', '原始判分矩阵：行为生产者，列为判官。虚线对角格为自评，仅作偏差诊断。颜色表示绝对评分，不表示增益；空格为缺失。');
    if (producers.length && judges.length) {
      const matrixRows = producers.map(producer => [producer, ...judges.map(judge => {
        const value = object(matrix[producer])[judge];
        const self = producer === judge;
        const cell = node('span', `matrix-cell ${self ? 'self' : ''}`, number(value));
        if (numeric(value) && !self) cell.style.backgroundColor = `rgba(168,229,203,${.025 + Math.max(0, Math.min(5, value)) / 5 * .19})`;
        if (self) cell.append(node('small', '', '自评'));
        cell.title = `${producer} → ${judge}：${number(value)}${self ? '（自评）' : ''}`;
        return cell;
      })]);
      matrixSection.append(table(['生产者 / 判官', ...judges], matrixRows, 'matrix-table'));
    } else matrixSection.append(node('p', 'muted', '此条目没有交叉判分矩阵。'));
    content.append(matrixSection);
    const checks = object(skill.assert);
    const assertions = detailSection('验收与解释边界');
    const list = node('ul', 'detail-small-list');
    append(list,
      node('li', '', numeric(checks['总']) && checks['总'] > 0 ? `确定性断言记录：${text(checks['过'] ?? '未知')} / ${text(checks['总'])}；这是历史累计记录，不代表每个模型或任务独立通过。` : '当前条目没有确定性断言记录。'),
      node('li', '', `同模型三模式字段齐全：${pair.length ? pair.join('、') : '无'}。字段齐全不代表评分口径可比。`),
      node('li', '', '成本、token、工具成功率与完整环境版本未在此快照提供；不据此判断性价比或替代关系。'),
      node('li', '', '模型名为快照中的原始别名，不等同于可复现的固定模型版本。')
    ); assertions.append(list); content.append(assertions);
    const gains = Object.entries(object(skill.gains));
    if (gains.length) {
      const legacy = detailSection('历史差值字段', '仅为兼容历史数据保留。旧评分口径与试验聚合存在限制，下表不作为净增益或退役依据。');
      legacy.append(table(['模型 | 任务', '旧 M2−M1', '旧 M2−M4', '旧 M4−M1'], gains.map(([key, value]) => [key, number(object(value)['M2-M1']), number(object(value)['M2-M4']), number(object(value)['M4-M1'])])));
      content.append(legacy);
    }
    const clues = array(skill['复盘线索']);
    if (clues.length) {
      const section = detailSection('历史复盘线索'); const items = node('ul', 'detail-small-list');
      clues.slice(0, 12).forEach(clue => items.append(node('li', '', typeof clue === 'string' ? clue : JSON.stringify(clue))));
      section.append(items); content.append(section);
    }
    const dialog = $('skill-dialog');
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
    $('close-dialog').focus({preventScroll: true});
  }

  async function load() {
    $('load-error').hidden = true;
    $('result-count').textContent = '正在载入技能…';
    $('retry').disabled = true;
    try {
      const response = await fetch('data.json', {cache: 'no-store'});
      if (!response.ok) throw new Error(`快照读取失败（HTTP ${response.status}）。`);
      const data = await response.json();
      if (!data || typeof data !== 'object' || !data.skills || typeof data.skills !== 'object' || Array.isArray(data.skills)) throw new Error('快照缺少有效的 skills 数据。');
      snapshot = data;
      entries = Object.entries(data.skills).filter(([, value]) => value && typeof value === 'object' && !Array.isArray(value)).map(([id, value]) => ({id, data: value}));
      renderSnapshot(); filterEntries();
    } catch (error) {
      $('skills-body').replaceChildren();
      $('pagination').hidden = true;
      $('load-error').hidden = false;
      $('error-message').textContent = `${error.message || '读取失败。'} 请通过本地 HTTP 服务打开页面，并确认 data.json 位于同一目录。`;
      $('result-count').textContent = '尚未载入数据';
      $('snapshot-time').textContent = '快照不可用';
      $('stats').replaceChildren(setStat('技能条目', '—', '数据未载入，数量未知'));
    } finally { $('retry').disabled = false; }
  }

  $('filters').addEventListener('submit', event => event.preventDefault());
  $('search').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => filterEntries(), 120); });
  ['model-filter', 'sort', 'paired-only'].forEach(id => $(id).addEventListener('change', () => filterEntries()));
  $('load-more').addEventListener('click', () => { visibleCount += PAGE_SIZE; renderSkills(); });
  $('group-filter').addEventListener('change', renderGroup);
  $('reset-filters').addEventListener('click', () => { $('filters').reset(); filterEntries(); $('search').focus(); });
  $('retry').addEventListener('click', load);
  $('close-dialog').addEventListener('click', () => $('skill-dialog').close());
  $('skill-dialog').addEventListener('close', () => { if (dialogTrigger?.isConnected) dialogTrigger.focus({preventScroll: true}); });
  $('skill-dialog').addEventListener('click', event => {
    if (event.target !== $('skill-dialog')) return;
    const rect = $('skill-dialog').getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) $('skill-dialog').close();
  });
  load();
})();
