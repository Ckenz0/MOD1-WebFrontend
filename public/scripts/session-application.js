// Adapt injected service methods to the current session without coupling to HTTP.
export function withSessionRenewal(client, { session, account }) {
  return Object.fromEntries(Object.entries(client).map(([name, method]) => [name, async (...args) => {
    if (args[0] && args[0] === session.getRequestToken() && session.shouldRefresh()) {
      const options = args.at(-1);
      args[0] = await account.accessToken({ signal: options?.signal });
    }
    return method.apply(client, args);
  }]));
}
