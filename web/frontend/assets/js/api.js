// Client HTTP minimal : même origine que le backend (T1), pas de base URL à
// configurer. Un seul point d'entrée (`request`) normalise les erreurs et
// gère le jeton d'accès ; les endpoints d'authentification sont de fines
// fonctions au-dessus.

const REFRESH_TOKEN_STORAGE_KEY = "ygnt.refreshToken";

let accessToken = null; // jamais persisté (mémoire uniquement)

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
}

function storeSession(tokens) {
  accessToken = tokens.access_token;
  localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, tokens.refresh_token);
}

export function clearSession() {
  accessToken = null;
  localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
}

async function parseErrorMessage(response) {
  try {
    const body = await response.json();
    return body.detail || "Une erreur inattendue est survenue.";
  } catch {
    return "Une erreur inattendue est survenue.";
  }
}

/**
 * @param {string} path
 * @param {{method?: string, body?: object, auth?: boolean, allowRetry?: boolean}} [options]
 */
async function request(path, options = {}) {
  const { method = "GET", body, auth = false, allowRetry = true } = options;

  const headers = { "Content-Type": "application/json" };
  if (auth) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Impossible de contacter le serveur.");
  }

  if (response.status === 401 && auth && allowRetry) {
    const renouvele = await tryRefresh();
    if (renouvele) {
      return request(path, { ...options, allowRetry: false });
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response));
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

async function tryRefresh() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return false;
  }
  try {
    const tokens = await request("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    });
    storeSession(tokens);
    return true;
  } catch {
    clearSession();
    return false;
  }
}

export async function login(email, motDePasse) {
  const tokens = await request("/auth/login", {
    method: "POST",
    body: { email, mot_de_passe: motDePasse },
  });
  storeSession(tokens);
}

export async function logout() {
  const refreshToken = getRefreshToken();
  clearSession();
  if (refreshToken) {
    try {
      await request("/auth/logout", { method: "POST", body: { refresh_token: refreshToken } });
    } catch {
      // La session locale est déjà effacée : un échec réseau ici n'empêche
      // pas l'utilisateur de se déconnecter côté client.
    }
  }
}

/** Tente de restaurer une session à partir du refresh token stocké. */
export async function restoreSession() {
  const restored = await tryRefresh();
  return restored;
}

export async function fetchCurrentUser() {
  return request("/auth/me", { auth: true });
}

/** Traduit la réponse de /auth/me vers la forme attendue par le store. */
export function toUserState(me) {
  return {
    utilisateurId: me.utilisateur_id,
    prenom: me.utilisateur_prenom,
    nom: me.utilisateur_nom,
    societeId: me.societe_id,
    societeNom: me.societe_nom,
    roles: me.roles,
  };
}

function buildQuery(params) {
  const query = new URLSearchParams();
  for (const [cle, valeur] of Object.entries(params)) {
    if (valeur !== undefined && valeur !== null && valeur !== "") {
      query.set(cle, valeur);
    }
  }
  const texte = query.toString();
  return texte ? `?${texte}` : "";
}

export async function listerPrestations(params = {}) {
  return request(`/prestations${buildQuery(params)}`, { auth: true });
}

export async function creerPrestation(payload) {
  return request("/prestations", { method: "POST", body: payload, auth: true });
}

export async function obtenirPrestation(id) {
  return request(`/prestations/${id}`, { auth: true });
}

export async function modifierPrestation(id, payload) {
  return request(`/prestations/${id}`, { method: "PUT", body: payload, auth: true });
}

export async function supprimerPrestation(id) {
  return request(`/prestations/${id}`, { method: "DELETE", auth: true });
}

export async function dupliquerPrestation(id) {
  return request(`/prestations/${id}/dupliquer`, { method: "POST", auth: true });
}

export async function changerStatutPrestation(id, statut) {
  return request(`/prestations/${id}/statut`, { method: "PATCH", body: { statut }, auth: true });
}
