/* Synthetic contract fixture, never an assessment by a real language model. */
const http = require('http');
const models = new Set(['gemini-3.5-flash-lite', 'mock-quota', 'mock-unavailable',
  'mock-timeout', 'mock-malformed', 'mock-truncated']);
http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const match = /^\/models\/([a-zA-Z0-9._-]+):generateContent$/.exec(url.pathname);
  function send(status, body) {
    res.writeHead(status, {'Content-Type': 'application/json'});
    res.end(JSON.stringify(body));
  }
  if (req.method !== 'POST' || !match || !models.has(match[1])) return send(501, {error: 'Outside fixture contract'});
  if (url.search || req.headers.authorization || req.headers['x-goog-api-key'] !== 'test-only-key') {
    return send(400, {error: 'Use only the synthetic key header; never forward a user token'});
  }
  const body = req.body;
  const config = body?.generationConfig;
  let input;
  try { input = JSON.parse(body.contents[0].parts[0].text); } catch (_) { return send(400, {error: 'Invalid context envelope'}); }
  const kinds = new Set(['access_anomalies', 'roles', 'access_revocation', 'teams', 'skills_map', 'training', 'initial_backlog']);
  if (!kinds.has(input.kind) || !input.context || !body.systemInstruction?.parts?.[0]?.text ||
      config?.candidateCount !== 1 || config?.responseFormat?.text?.mimeType !== 'APPLICATION_JSON' ||
      !config?.responseFormat?.text?.schema || !Number.isInteger(config.maxOutputTokens) ||
      config.maxOutputTokens < 256 || config.maxOutputTokens > 8192) return send(400, {error: 'Invalid structured output contract'});
  const model = match[1];
  if (model === 'mock-quota') return send(429, {error: {message: 'Synthetic quota fixture'}});
  if (model === 'mock-unavailable') return send(503, {error: {message: 'Synthetic unavailable fixture'}});
  if (model === 'mock-malformed') { res.writeHead(200, {'Content-Type': 'application/json'}); return res.end('{broken'); }
  const evidence = input.kind === 'access_anomalies'
    ? (input.context.audit_events || []).slice(0, 1).map(event => event.id)
    : input.kind === 'initial_backlog' ? ['project.description']
    : (input.context.evidence || []).slice(0, 1);
  const proposal = {summary: 'Análise fictícia sem alterações',
    justification: 'Fixture de transporte: nenhuma sugestão foi gerada por um modelo real.',
    evidence, suggestions: []};
  const response = {candidates: [{finishReason: model === 'mock-truncated' ? 'MAX_TOKENS' : 'STOP',
    content: {role: 'model', parts: [{text: JSON.stringify(proposal)}]}}]};
  if (model === 'mock-timeout') return setTimeout(() => send(200, response), 2500);
  return send(200, response);
}).listen(process.env.PORT || 4010);
