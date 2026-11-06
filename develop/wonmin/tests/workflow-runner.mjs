// Local test adapter: executes the checked-in Code and expression bodies.
// This is NOT n8n: Header Auth, item linking and node/runtime compatibility need n8n tests.
import vm from 'node:vm';

export function code(node, input, history = {}, env = {}, executionContext = {}) {
  const context = {
    $json: input,
    $input: { first: () => ({ json: input }) },
    $env: env,
    $workflow: executionContext.workflow ?? {},
    $: name => ({ first: () => ({ json: history[name] }) }),
  };
  return JSON.parse(JSON.stringify(vm.runInNewContext(
    `(function () { ${node.parameters.jsCode}\n })()`, context, { timeout: 500 },
  )))[0].json;
}

export async function run(workflow, body, env, credentials, transport = fetch) {
  const history = {};
  const nodes = new Map(workflow.nodes.map(n => [n.name, n]));
  let node = workflow.nodes.find(n => n.type.endsWith('.webhook') || n.type.endsWith('.errorTrigger'));
  const errorMode = node?.type.endsWith('.errorTrigger');
  let value = errorMode ? body : { body };
  const trace = [];
  const expression = source => {
    if (typeof source !== 'string' || !source.startsWith('={{')) return source;
    return vm.runInNewContext(source.slice(3, -2), {
      $json: value, $env: env,
      $: name => ({ first: () => ({ json: history[name] }) }),
    }, { timeout: 500 });
  };
  for (let count = 0; count < 40; count++) {
    trace.push(node.name);
    let output = 0;
    if (node.type.endsWith('.code')) value = code(node, value, history, env, { workflow: { id: workflow.id, name: workflow.name } });
    else if (node.type.endsWith('.if')) {
      output = expression(node.parameters.conditions.conditions[0].leftValue) === true ? 0 : 1;
    } else if (node.type.endsWith('.httpRequest')) {
      const key = node.credentials.httpHeaderAuth.name;
      const credential = credentials[key];
      if (!credential) throw Error('Missing local credential mapping');
      const options = node.parameters.options;
      try {
        const response = await transport(expression(node.parameters.url), {
          method: node.parameters.method,
          headers: { 'content-type': 'application/json', [credential.header]: credential.value },
          body: expression(node.parameters.jsonBody),
          signal: AbortSignal.timeout(options.timeout),
          redirect: 'manual',
        });
        value = { statusCode: response.status, headers: Object.fromEntries(response.headers), body: await response.json() };
      } catch {
        if (node.onError !== 'continueRegularOutput') throw Error('Unhandled HTTP failure');
        value = { error: 'local_transport_failure' };
      }
    } else if (node.type.endsWith('.wait')) {
      const seconds = expression(node.parameters.amount);
      if (node.parameters.unit !== 'seconds' || !Number.isFinite(seconds) || seconds < 0 || seconds > 0.2) {
        throw Error('Unsupported local Wait parameters');
      }
      await new Promise(resolve => setTimeout(resolve, seconds * 1000));
    } else if (node.type.endsWith('.respondToWebhook')) {
      return { status: expression(node.parameters.options.responseCode),
        body: JSON.parse(JSON.stringify(expression(node.parameters.responseBody))), history, trace };
    } else if (!node.type.endsWith('.webhook') && !node.type.endsWith('.errorTrigger')) throw Error('Unsupported adapter node');
    history[node.name] = value;
    const edge = workflow.connections[node.name]?.main[output];
    if (errorMode && !edge && node.type.endsWith('.code')) return { body: value, history, trace };
    if (edge?.length !== 1) throw Error('Expected exactly one next node');
    node = nodes.get(edge[0].node);
  }
  throw Error('Local adapter step limit exceeded');
}
