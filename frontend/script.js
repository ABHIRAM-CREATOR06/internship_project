const moneyFields = [
  "income_annum",
  "loan_amount",
  "residential_assets_value",
  "commercial_assets_value",
  "luxury_assets_value",
  "bank_asset_value",
];

const elements = {
  healthBadge: document.querySelector("#healthBadge"),
  rowsValue: document.querySelector("#rowsValue"),
  nullValue: document.querySelector("#nullValue"),
  approvedValue: document.querySelector("#approvedValue"),
  rejectedValue: document.querySelector("#rejectedValue"),
  loanForm: document.querySelector("#loanForm"),
  predictButton: document.querySelector("#predictButton"),
  predictionText: document.querySelector("#predictionText"),
  confidenceText: document.querySelector("#confidenceText"),
  confidenceBar: document.querySelector("#confidenceBar"),
  explanationText: document.querySelector("#explanationText"),
  assistantForm: document.querySelector("#assistantForm"),
  assistantLog: document.querySelector("#assistantLog"),
  queryForm: document.querySelector("#queryForm"),
  queryLog: document.querySelector("#queryLog"),
};

let latestPredictionContext = null;

function formatNumber(value) {
  return new Intl.NumberFormat("en-IN").format(value);
}

function setHealth(status) {
  elements.healthBadge.textContent = status ? "Running" : "Offline";
  elements.healthBadge.classList.toggle("offline", !status);
}

async function loadHealth() {
  try {
    const response = await fetch("/health");
    setHealth(response.ok);
  } catch {
    setHealth(false);
  }
}

async function loadStats() {
  try {
    const response = await fetch("/stats");
    const stats = await response.json();
    elements.rowsValue.textContent = formatNumber(stats.rows);
    elements.nullValue.textContent = formatNumber(stats.null_values);
    elements.approvedValue.textContent = formatNumber(stats.approved);
    elements.rejectedValue.textContent = formatNumber(stats.rejected);
  } catch {
    elements.rowsValue.textContent = "--";
    elements.nullValue.textContent = "--";
    elements.approvedValue.textContent = "--";
    elements.rejectedValue.textContent = "--";
  }
}

function formToPayload(form) {
  const data = new FormData(form);
  const payload = {
    education: data.get("education"),
    self_employed: data.get("self_employed"),
    include_explanation: true,
  };

  for (const [key, value] of data.entries()) {
    if (key in payload) continue;
    payload[key] = Number(value);
  }

  for (const key of moneyFields) {
    payload[key] = Number(payload[key]);
  }

  return payload;
}

function showPrediction(result) {
  const confidence = Number(result.confidence ?? Math.round(result.probability * 100));
  elements.predictionText.textContent = result.prediction;
  elements.predictionText.className = result.prediction === "Approved" ? "approved" : "rejected";
  elements.confidenceText.textContent = `${confidence}%`;
  elements.confidenceBar.style.width = `${Math.max(0, Math.min(100, confidence))}%`;
  elements.explanationText.textContent = result.explanation || "Prediction completed.";
  latestPredictionContext = {
    prediction: result.prediction,
    confidence,
    approved_probability: result.approved_probability,
    rejected_probability: result.rejected_probability,
    inputs: formToPayload(elements.loanForm),
  };
}

function renderAssistantMessage(question, answer) {
  elements.assistantLog.innerHTML = "";

  const questionNode = document.createElement("p");
  const questionLabel = document.createElement("strong");
  questionLabel.textContent = "You:";
  questionNode.append(questionLabel, ` ${question}`);

  const answerNode = document.createElement("p");
  const answerLabel = document.createElement("strong");
  answerLabel.textContent = "BankPulse:";
  answerNode.append(answerLabel, ` ${answer}`);

  elements.assistantLog.append(questionNode, answerNode);
}

function renderQueryMessage(query, answer) {
  elements.queryLog.innerHTML = "";

  const queryNode = document.createElement("p");
  const queryLabel = document.createElement("strong");
  queryLabel.textContent = "Query:";
  queryNode.append(queryLabel, ` ${query}`);

  const answerNode = document.createElement("p");
  const answerLabel = document.createElement("strong");
  answerLabel.textContent = "Answer:";
  answerNode.append(answerLabel, ` ${answer}`);

  elements.queryLog.append(queryNode, answerNode);
}

elements.loanForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  elements.predictButton.disabled = true;
  elements.predictButton.textContent = "Predicting";

  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formToPayload(elements.loanForm)),
    });
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Prediction failed");
    }

    showPrediction(result);
  } catch (error) {
    elements.predictionText.textContent = "Unable to predict";
    elements.predictionText.className = "rejected";
    elements.confidenceText.textContent = "--%";
    elements.confidenceBar.style.width = "0%";
    elements.explanationText.textContent = error.message;
  } finally {
    elements.predictButton.disabled = false;
    elements.predictButton.textContent = "Predict";
  }
});

async function askAssistant(question) {
  const input = elements.assistantForm.elements.question;
  if (!question) return;

  elements.assistantLog.textContent = "Thinking...";

  try {
    const response = await fetch("/assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, context: latestPredictionContext }),
    });
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Assistant unavailable");
    }

    renderAssistantMessage(question, result.answer);
    input.value = "";
  } catch (error) {
    renderAssistantMessage(question, error.message);
  }
}

async function askQuery(queryText) {
  if (!queryText) return;

  elements.queryLog.textContent = "Querying dataset...";

  try {
    const response = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText }),
    });
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Query failed");
    }

    renderQueryMessage(queryText, result.answer);
    elements.queryForm.elements.query.value = "";
  } catch (error) {
    renderQueryMessage(queryText, error.message);
  }
}

elements.assistantForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = elements.assistantForm.elements.question.value.trim();
  askAssistant(question);
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    askAssistant(button.dataset.question);
  });
});

elements.queryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const queryText = elements.queryForm.elements.query.value.trim();
  askQuery(queryText);
});

document.querySelectorAll("[data-query]").forEach((button) => {
  button.addEventListener("click", () => {
    askQuery(button.dataset.query);
  });
});

loadHealth();
loadStats();

