// Store applicatif minimal : un seul état, un pub/sub simple.
// Pas de framework de gestion d'état — inutile pour la surface actuelle
// (session + garde-fous de chargement/erreur). À faire grossir si un futur
// module en a réellement besoin, pas par anticipation.

const listeners = new Set();

const state = {
  status: "booting", // "booting" | "authenticated" | "anonymous"
  user: null, // { utilisateurId, prenom, nom, societeId, societeNom, roles }
  loading: false,
  globalError: null,
};

function notify() {
  for (const listener of listeners) {
    listener(state);
  }
}

export function getState() {
  return state;
}

export function subscribe(listener) {
  listeners.add(listener);
  listener(state);
  return () => listeners.delete(listener);
}

export function setUser(user) {
  state.user = user;
  state.status = user ? "authenticated" : "anonymous";
  notify();
}

export function setLoading(loading) {
  state.loading = loading;
  notify();
}

export function setGlobalError(message) {
  state.globalError = message;
  notify();
}

export function clearGlobalError() {
  state.globalError = null;
  notify();
}
