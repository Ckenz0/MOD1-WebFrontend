// Shared boundary errors: no transport or browser dependencies.
const platformMessages = {
  unauthorized: "Sua sessão terminou. Entre novamente para continuar.",
  forbidden: "Você não tem permissão para esta ação. Atualize seus acessos.",
  "not-found": "Este registro não está disponível para sua conta.",
  conflict: "Os dados mudaram ou esta operação não é permitida no estado atual. Atualize e tente novamente.",
  validation: "Confira os campos informados e tente novamente.",
  unavailable: "O serviço está indisponível ou ainda não foi configurado. Tente novamente mais tarde.",
  network: "Não foi possível conectar ao serviço. Confira a conexão e tente novamente.",
  timeout: "O serviço demorou para responder. Confira os dados antes de tentar novamente.",
  cancelled: "A solicitação foi cancelada.",
  "invalid-response": "Não foi possível confirmar os dados recebidos. Atualize e tente novamente.",
};
export class PlatformApiError extends Error {
  constructor(kind) { super(platformMessages[kind] || platformMessages.unavailable); this.name = "PlatformApiError"; this.kind = kind; }
}

const identityMessages = {
  credentials: "E-mail ou senha inválidos. Confira os dados e tente novamente.",
  unauthorized: "Sua sessão terminou. Entre novamente para continuar.",
  validation: "Confira os dados informados e tente novamente.",
  unavailable: "O serviço está indisponível no momento. Tente novamente em instantes.",
  network: "Não foi possível conectar ao serviço. Confira a conexão e tente novamente.",
  timeout: "O serviço demorou para responder. Tente novamente.",
  "invalid-response": "Não foi possível confirmar os dados recebidos. Tente novamente.",
  cancelled: "A solicitação foi cancelada.",
  "password-rejected": "Não foi possível alterar a senha. Confira a senha atual e escolha uma nova senha diferente.",
};

export class ApiError extends Error {
  constructor(kind) {
    super(identityMessages[kind]);
    this.name = "ApiError";
    this.kind = kind;
  }
}


const projectsMessages = {
  unauthorized: "Sua sessão terminou. Entre novamente para continuar.",
  validation: "Confira o nome e a descrição do projeto e tente novamente.",
  "not-found": "Este projeto não está disponível para sua conta. Volte para a lista.",
  unavailable: "O serviço de projetos está indisponível. Tente novamente em instantes.",
  network: "Não foi possível conectar ao serviço de projetos. Confira a conexão e tente novamente.",
  timeout: "O serviço de projetos demorou para responder. Atualize a lista antes de tentar novamente.",
  "invalid-response": "Não foi possível confirmar os dados do projeto. Tente novamente.",
  cancelled: "A solicitação foi cancelada.",
  forbidden: "Você não tem permissão para esta ação. Atualize os acessos do projeto.",
  conflict: "Não foi possível alterar este vínculo. O proprietário é protegido e contas já vinculadas não precisam de novo convite.",
};

export class ProjectsApiError extends Error {
  constructor(kind) { super(projectsMessages[kind]); this.name = "ProjectsApiError"; this.kind = kind; }
}


const backlogMessages = {
  unauthorized: "Sua sessão terminou. Entre novamente para continuar.",
  validation: "Confira o título e os campos da história e tente novamente.",
  "not-found": "Esta história não está disponível para sua conta. Volte para a lista.",
  unavailable: "O serviço de backlog está indisponível. Tente novamente em instantes.",
  network: "Não foi possível conectar ao serviço de backlog. Confira a conexão e tente novamente.",
  timeout: "O serviço de backlog demorou para responder. Atualize a lista antes de tentar novamente.",
  "invalid-response": "Não foi possível confirmar os dados da história. Tente novamente.",
  cancelled: "A solicitação foi cancelada.",
  forbidden: "Você não tem permissão para esta ação no backlog. Volte ao projeto para conferir seus acessos.",
};

export class BacklogApiError extends Error {
  constructor(kind) { super(backlogMessages[kind]); this.name = "BacklogApiError"; this.kind = kind; }
}
