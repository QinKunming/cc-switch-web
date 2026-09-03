// Form-logic harness: runs the inline script from static/index.html against a
// minimal DOM stub, then exercises the collect functions with populated fields.
// Usage: node tests/frontend_logic_test.js
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'static', 'index.html'), 'utf-8');
// multiple inline scripts exist (FOUC theme setter + main); the main one is last
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const js = blocks[blocks.length - 1];

function fakeEl() {
  return {
    value: '', checked: false, style: {}, dataset: {}, textContent: '', innerHTML: '',
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
    insertAdjacentHTML() {}, appendChild() {}, remove() {},
    querySelector: () => null, querySelectorAll: () => [],
    closest: () => null, disabled: false,
  };
}
const elements = {};
const doc = {
  documentElement: { dataset: {} },
  getElementById: id => elements[id] || (elements[id] = fakeEl()),
  querySelectorAll: () => [],
  createElement: () => fakeEl(),
  addEventListener() {},
  body: { appendChild() {} },
};

const setup = `
  const document = ${JSON.stringify('doc-placeholder')};
`;

// Build the evaluated scope via Function so declarations stay inside; return hooks.
const harness = new Function('document', 'fetch', 'confirm', 'localStorage', `
  ${js}
  return {
    tomlGet, tomlSet, tomlGetInt, MODEL_FIELDS,
    setEditModels: v => { _editModelsRaw = v; },
    collectModelEntries, collectCodexFormData, collectGrokFormData,
    collectOpencodeFormData, collectHermesFormData, collectPiFormData,
    collectCdFormData, collectGeminiFormData,
    toggleTheme, applyThemeLabel, fetchAndShowModels,
  };
`);
const store = {};
const ls = { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
const api = harness(doc, async () => { throw new Error('no fetch in test'); }, () => true, ls);

let failures = 0;
function ok(cond, label) {
  if (cond) { console.log('  ok - ' + label); }
  else { failures++; console.log('  FAIL - ' + label); }
}

// --- pure helpers ---
ok(api.tomlGet('model = "gpt-5.2"', 'model') === 'gpt-5.2', 'tomlGet reads string');
ok(api.tomlSet('model = "a"\nmodel_reasoning_effort = "low"', 'model_reasoning_effort', 'high')
   .includes('model_reasoning_effort = "high"'), 'tomlSet replaces value');
ok(api.tomlSet('disable_response_storage = true', 'disable_response_storage', 'false')
   .includes('disable_response_storage = false'), 'tomlSet keeps bools bare');

// --- codex collect ---
const g = id => doc.getElementById(id);
g('f_id').value = 'my-codex'; g('f_name').value = 'My Codex';
g('f_base_url').value = 'https://codex.example.com';
g('f_api_key').value = 'sk-123';
g('f_model').value = 'gpt-5.2';
g('f_effort').value = 'high';
g('f_drs').checked = true;
g('f_raw').value = 'model_provider = "custom"\nmodel = ""\nmodel_reasoning_effort = "high"\ndisable_response_storage = true\n\n[model_providers.custom]\nname = ""\nbase_url = ""\nwire_api = "responses"\nrequires_openai_auth = true\n';
g('f_category').value = 'custom'; g('f_website').value = '';
const codex = api.collectCodexFormData();
ok(codex.settings_config.auth.OPENAI_API_KEY === 'sk-123', 'codex auth key collected');
ok(codex.settings_config.config.includes('base_url = "https://codex.example.com"'), 'codex base_url saved as-is (no /v1 auto-appended)');
ok(codex.settings_config.config.includes('model = "gpt-5.2"'), 'codex model injected');
ok(codex.settings_config.config.includes('name = "My Codex"'), 'codex provider name injected');

// --- model entries (openclaw-shaped vs opencode-shaped, extras preserved) ---
function fakeEntry(fields) {
  const el = fakeEl();
  el.querySelector = sel => {
    return { value: String(fields[sel.slice(1)] ?? '') };
  };
  return el;
}
doc.querySelectorAll = sel => sel === '.model-entry' ? [
  fakeEntry({ 'me-id': 'm1', 'me-name': 'M1', 'me-cw': '200000' }),
  fakeEntry({ 'me-id': 'm2', 'me-name': '', 'me-cw': '' }),
] : [];
let entries = api.collectModelEntries('openclaw');
ok(entries[0].contextWindow === 200000 && entries[0].name === 'M1', 'openclaw entries use contextWindow');
ok(!('limit' in entries[0]), 'openclaw entries carry no limit key');

doc.querySelectorAll = sel => sel === '.model-entry' ? [
  fakeEntry({ 'me-id': 'kimi-k3', 'me-name': 'K3', 'me-cw': '1048576', 'me-out': '131072' }),
] : [];
api.setEditModels({ 'kimi-k3': { name: 'Kimi K3', limit: { context: 0, output: 0 }, toolNote: 'keep' } });
entries = api.collectModelEntries('opencode');
ok(entries[0].limit && entries[0].limit.context === 1048576 && entries[0].limit.output === 131072, 'opencode limits collected');
ok(entries[0].toolNote === 'keep', 'opencode stored extras preserved');

api.setEditModels({ 'm9': { id: 'm9', compat: { x: 1 } } });
doc.querySelectorAll = sel => sel === '.model-entry' ? [fakeEntry({ 'me-id': 'm9' })] : [];
entries = api.collectModelEntries('pi');
ok(entries[0].compat && entries[0].compat.x === 1, 'pi compat preserved through edit');

// --- grok collect ---
g('f_profile').value = 'grok-4.5'; g('f_model').value = 'grok-4.5';
g('f_base_url').value = 'https://gr.example.com/'; g('f_api_key').value = 'k';
g('f_backend').value = 'responses'; g('f_cw').value = '500000';
const grok = api.collectGrokFormData();
ok(grok.settings_config.config.startsWith('[models]\ndefault = "grok-4.5"'), 'grok TOML header');
ok(grok.settings_config.config.includes('context_window = 500000'), 'grok context_window int');
ok(grok.settings_config.config.includes('base_url = "https://gr.example.com/"'), 'grok base_url saved as-is (trailing slash kept, no /v1)');

// --- opencode collect ---
g('f_id').value = 'oc'; g('f_name').value = 'OC'; g('f_npm').value = '@ai-sdk/openai-compatible';
g('f_display').value = 'OC Display'; g('f_base_url').value = 'https://oc.example.com/v1'; g('f_api_key').value = 'k2';
api.setEditModels({});
doc.querySelectorAll = sel => sel === '.model-entry' ? [fakeEntry({ 'me-id': 'm1', 'me-name': 'M1', 'me-cw': '1', 'me-out': '2' })] : [];
const oc = api.collectOpencodeFormData();
ok(oc.settings_config.models.m1 && oc.settings_config.models.m1.name === 'M1', 'opencode models dict keyed by id');
ok(oc.settings_config.models.m1.limit.context === 1 && oc.settings_config.models.m1.limit.output === 2, 'opencode limit nesting');
ok(!('id' in oc.settings_config.models.m1), 'opencode id stripped from entry');
ok(oc.settings_config.options.baseURL === 'https://oc.example.com/v1', 'opencode options.baseURL');

// --- claude-desktop collect ---
g('f_id').value = 'cd'; g('f_name').value = 'CD'; g('f_base_url').value = 'https://cd.example.com';
g('f_api_key').value = 'tok'; g('f_key_field').value = 'ANTHROPIC_AUTH_TOKEN';
doc.querySelectorAll = sel => sel === '.model-entry' ? [fakeEntry({ 'me-id': 'claude-sonnet-5' })] : [];
const cd = api.collectCdFormData();
ok(cd.settings_config.env.ANTHROPIC_AUTH_TOKEN === 'tok', 'cd bearer token');
ok(JSON.stringify(cd.settings_config.inferenceModels) === '["claude-sonnet-5"]', 'cd inferenceModels string list');

// --- gemini collect ---
g('f_id').value = 'gm'; g('f_name').value = 'GM'; g('f_base_url').value = 'https://gm.example.com';
g('f_api_key').value = 'gk'; g('f_model').value = 'gemini-3.6-flash';
const gm = api.collectGeminiFormData();
ok(gm.settings_config.env.GEMINI_MODEL === 'gemini-3.6-flash' && gm.settings_config.env.GEMINI_API_KEY === 'gk', 'gemini env collected');

// --- theme toggle ---
doc.documentElement.dataset.theme = 'dark';
api.applyThemeLabel();
ok(doc.getElementById('themeToggle').textContent === '☀️', 'dark theme shows sun icon');
api.toggleTheme();
ok(doc.documentElement.dataset.theme === 'light' && store['ccsw-theme'] === 'light', 'toggle switches to light and persists');
api.applyThemeLabel();
ok(doc.getElementById('themeToggle').textContent === '🌙', 'light theme shows moon icon');
api.toggleTheme();
ok(store['ccsw-theme'] === 'dark', 'toggle back to dark persists');

// --- fetchAndShowModels success path: dropdown renders AND scrolls into view ---
// 回归：下拉框锚在 Models 组底部，滚动弹窗里可能开在可视区外且开关式按钮会
// 吞掉后续点击——显示时必须滚入视野（revealDropdown）。
(async () => {
  let scrolled = 0;
  const dd = fakeEl();
  const shown = new Set();
  dd.classList = {
    add: c => shown.add(c), remove: c => shown.delete(c),
    toggle: c => shown.has(c) ? shown.delete(c) : shown.add(c),
    contains: c => shown.has(c),
  };
  dd.scrollIntoView = () => { scrolled++; };
  const doc2 = {
    ...doc,
    getElementById: id => id === 'dd_oc_models' ? dd : doc.getElementById(id),
    querySelectorAll: () => [],
    // 页面的 esc() 依赖 textContent -> innerHTML 的真实 DOM 行为，桩上补齐
    createElement: () => {
      const el = fakeEl();
      Object.defineProperty(el, 'textContent', {
        get: () => el.innerHTML,
        set: v => { el.innerHTML = String(v); },
      });
      return el;
    },
  };
  const mockFetch = async () => ({
    ok: true, status: 200,
    json: async () => ({ models: ['deepseek-v4-flash', 'deepseek-v4-pro'] }),
  });
  const api2 = harness(doc2, mockFetch, () => true, ls);
  await api2.fetchAndShowModels();
  ok(shown.has('show'), 'dropdown shown after successful fetch');
  ok(dd.innerHTML.includes('deepseek-v4-flash') && dd.innerHTML.includes('deepseek-v4-pro'),
     'fetched models rendered into dropdown');
  ok(scrolled >= 1, 'dropdown scrolled into view (revealDropdown)');

  if (failures) { console.log(failures + ' FAILURE(S)'); process.exit(1); }
  console.log('FRONTEND LOGIC TESTS PASSED');
})();
