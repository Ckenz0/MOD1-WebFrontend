import { el, action, form } from "./workspace-view.js";

// Public recovery credentials live only in this view's closure and POST bodies.
export function createPublicAuthController({ client, account, onEnter, onBack, onIdentity }) {
  const root = el("section", null, { id: "recovery-view", class: "auth-panel", hidden: true });
  const title = el("h1", "", { tabindex: "-1" });
  const notice = el("p", "", { id: "recovery-status", role: "status", "aria-live": "polite", hidden: true });
  const content = el("div");
  root.append(title, notice, content, action("Voltar para entrar", () => { clear(); account.logout(); onBack(); }));
  document.getElementById("main").append(root);
  let generation = 0, controller = null, secretToken = null, busy = false;
  function clear() { generation++; controller?.abort(); controller = null; secretToken = null; busy = false; root.hidden = true; content.replaceChildren(); notice.textContent = ""; }
  function enter(label) { clear(); onEnter(); root.hidden = false; title.textContent = label; title.focus(); }
  function status(text) { notice.textContent = text; notice.hidden = !text; }
  async function run(work) {
    if (busy || root.hidden) return;
    const current = generation; controller = new AbortController(); busy = true;
    root.setAttribute("aria-busy", "true");
    for (const button of root.querySelectorAll("button")) button.disabled = true;
    try { await work(controller.signal, () => current === generation); }
    catch (error) { if (current === generation && error.kind !== "cancelled") status(error.message || "Não foi possível concluir. Tente novamente."); }
    finally { if (current === generation) { busy = false; root.setAttribute("aria-busy", "false"); for (const button of root.querySelectorAll("button")) button.disabled = false; } }
  }
  function openRecovery() {
    enter("Recuperar acesso");
    content.append(el("p", "Solicite um link temporário para definir uma nova senha.", { class: "intro" }));
    const f = form("recovery", [{ name: "email", label: "E-mail para recuperação", type: "email", required: true }], "Solicitar link de recuperação", values => run(async (signal, valid) => {
      await client.request("POST", "/auth/password/reset/request", null, { email: values.email }, { signal });
      if (valid()) { f.reset(); status("Se o endereço estiver cadastrado, você receberá as instruções de recuperação."); }
    })); content.append(f.node);
  }
  function openMfa() {
    enter("Confirmar segundo fator");
    const f = form("login-factor", [
      { name: "code", label: "Código do autenticador ou de recuperação", required: true, autocomplete: "one-time-code" },
      { name: "recovery", label: "Usar código de recuperação", type: "checkbox" },
    ], "Confirmar acesso", values => run(async (signal, valid) => {
      const user = await account.verifyMfa(values.code.trim(), { recovery: values.recovery, signal });
      if (valid()) { clear(); onIdentity(user); }
    })); content.append(f.node);
  }
  function consumeLink() {
    const params = new URLSearchParams(location.hash.slice(1));
    const reset = params.get("recovery"), verify = params.get("verify-email");
    if (!reset && !verify) return false;
    history.replaceState(null, "", location.pathname + location.search);
    enter(reset ? "Definir nova senha" : "Confirmar e-mail"); secretToken = reset || verify;
    if (reset) {
      const f = form("reset", [
        { name: "new_password", label: "Nova senha", type: "password", required: true, minLength: 12, autocomplete: "new-password" },
        { name: "confirmation", label: "Confirme a nova senha", type: "password", required: true, autocomplete: "new-password" },
        { name: "second_factor", label: "Código do autenticador (se MFA estiver ativo)", autocomplete: "one-time-code" },
        { name: "recovery_code", label: "Código de recuperação (alternativa ao autenticador)", autocomplete: "off" },
      ], "Salvar nova senha", values => run(async (signal, valid) => {
        if (values.new_password !== values.confirmation) { status("As senhas precisam ser iguais."); return; }
        const body = { token: secretToken, new_password: values.new_password };
        if (values.second_factor.trim()) body.second_factor = values.second_factor.trim();
        if (values.recovery_code.trim()) body.recovery_code = values.recovery_code.trim();
        await client.request("POST", "/auth/password/reset/confirm", null, body, { signal });
        if (valid()) { secretToken = null; f.reset(); content.replaceChildren(el("p", "Senha alterada. Entre novamente com a nova senha.")); status("Suas sessões anteriores foram encerradas."); }
      })); content.append(f.node);
    } else {
      content.append(action("Confirmar meu e-mail", () => run(async (signal, valid) => {
        await client.request("POST", "/auth/email/confirm", null, { token: secretToken }, { signal });
        if (valid()) { secretToken = null; content.replaceChildren(el("p", "Endereço de e-mail confirmado.")); }
      })));
    }
    return true;
  }
  return { clear, openRecovery, openMfa, consumeLink };
}
