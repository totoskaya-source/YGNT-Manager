import * as api from "../api.js";
import { createSpinner } from "../components/spinner.js";
import { navigate } from "../router.js";
import { setGlobalError, setLoading, setUser } from "../state.js";

async function loadCurrentUser() {
  const me = await api.fetchCurrentUser();
  setUser(api.toUserState(me));
}

export function renderLoginView(root) {
  const screen = document.createElement("div");
  screen.className = "login-screen";

  const card = document.createElement("div");
  card.className = "card login-card";

  const title = document.createElement("h1");
  title.textContent = "Connexion — YGNT Manager";

  const form = document.createElement("form");
  form.noValidate = true;

  const emailField = buildField("email", "Email", "email");
  const passwordField = buildField("mot-de-passe", "Mot de passe", "password");

  const errorMessage = document.createElement("p");
  errorMessage.className = "form-error";
  errorMessage.hidden = true;

  const submitButton = document.createElement("button");
  submitButton.type = "submit";
  submitButton.className = "button";
  submitButton.textContent = "Se connecter";

  form.append(emailField.wrapper, passwordField.wrapper, errorMessage, submitButton);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorMessage.hidden = true;
    submitButton.disabled = true;
    const spinner = createSpinner();
    submitButton.append(spinner);
    setLoading(true);

    try {
      await api.login(emailField.input.value, passwordField.input.value);
      await loadCurrentUser();
      navigate("/");
    } catch (error) {
      if (error.status === 401) {
        errorMessage.textContent = "Email ou mot de passe incorrect.";
        errorMessage.hidden = false;
      } else {
        setGlobalError(error.message);
      }
    } finally {
      submitButton.disabled = false;
      spinner.remove();
      setLoading(false);
    }
  });

  card.append(title, form);
  screen.append(card);
  root.append(screen);
}

function buildField(id, labelText, type) {
  const wrapper = document.createElement("div");
  wrapper.className = "form-field";

  const label = document.createElement("label");
  label.setAttribute("for", id);
  label.textContent = labelText;

  const input = document.createElement("input");
  input.id = id;
  input.name = id;
  input.type = type;
  input.required = true;
  input.autocomplete = type === "password" ? "current-password" : "username";

  wrapper.append(label, input);
  return { wrapper, input };
}
