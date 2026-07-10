const queryInput = document.getElementById("queryInput");
const topKInput = document.getElementById("topKInput");
const minSimilarityInput = document.getElementById("minSimilarityInput");
const askButton = document.getElementById("askButton");
const insufficientButton = document.getElementById("insufficientButton");
const statusMessage = document.getElementById("statusMessage");
const resultPanel = document.getElementById("resultPanel");
const answerStatus = document.getElementById("answerStatus");
const answerText = document.getElementById("answerText");
const sourcesList = document.getElementById("sourcesList");

function setLoading(isLoading) {
  askButton.disabled = isLoading;
  insufficientButton.disabled = isLoading;
  statusMessage.textContent = isLoading ? "Generating source-grounded answer..." : "";
}

function buildAskPayload() {
  const payload = {
    query: queryInput.value.trim(),
    top_k: Number.parseInt(topKInput.value, 10) || 3,
  };

  const minSimilarityValue = minSimilarityInput.value.trim();

  if (minSimilarityValue !== "") {
    payload.min_similarity_score = Number.parseFloat(minSimilarityValue);
  }

  return payload;
}

function renderAnswerWithCitations(container, answer) {
  container.textContent = "";

  const parts = answer.split(/(\[S\d+\])/g);

  for (const part of parts) {
    if (!part) {
      continue;
    }

    if (/^\[S\d+\]$/.test(part)) {
      const citation = document.createElement("span");
      citation.className = "citation-badge";
      citation.textContent = part;
      container.appendChild(citation);
    } else {
      container.appendChild(document.createTextNode(part));
    }
  }
}

function renderSources(sources) {
  sourcesList.textContent = "";

  if (!sources || sources.length === 0) {
    const emptyMessage = document.createElement("p");
    emptyMessage.className = "source-meta";
    emptyMessage.textContent = "No source evidence was returned for this answer.";
    sourcesList.appendChild(emptyMessage);
    return;
  }

  for (const source of sources) {
    const card = document.createElement("article");
    card.className = "source-card";

    const title = document.createElement("div");
    title.className = "source-title";

    const sourceId = document.createElement("span");
    sourceId.className = "source-id";
    sourceId.textContent = source.source_id || "Source";

    const fileName = document.createElement("span");
    fileName.textContent = source.source || "Unknown source";

    title.appendChild(sourceId);
    title.appendChild(fileName);

    const chunkId = document.createElement("p");
    chunkId.className = "source-meta";
    chunkId.textContent = `Chunk: ${source.chunk_id || "N/A"}`;

    const similarity = document.createElement("p");
    similarity.className = "source-meta";

    if (typeof source.similarity_score === "number") {
      similarity.textContent = `Similarity score: ${source.similarity_score.toFixed(4)}`;
    } else {
      similarity.textContent = "Similarity score: N/A";
    }

    const preview = document.createElement("p");
    preview.className = "source-preview";
    preview.textContent = source.text_preview || "No preview available.";

    card.appendChild(title);
    card.appendChild(chunkId);
    card.appendChild(similarity);
    card.appendChild(preview);

    sourcesList.appendChild(card);
  }
}

function renderResult(data) {
  resultPanel.classList.remove("hidden");

  answerStatus.textContent = data.answer_status;

  if (data.answer_status === "insufficient_evidence") {
    answerStatus.classList.add("insufficient");
  } else {
    answerStatus.classList.remove("insufficient");
  }

  renderAnswerWithCitations(answerText, data.answer);
  renderSources(data.sources);
}

async function askQuestion() {
  const payload = buildAskPayload();

  if (!payload.query) {
    statusMessage.textContent = "Please enter a programming question.";
    return;
  }

  setLoading(true);

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText);
    }

    const data = await response.json();
    renderResult(data);
  } catch (error) {
    resultPanel.classList.add("hidden");
    statusMessage.textContent = `Request failed: ${error.message}`;
  } finally {
    setLoading(false);
  }
}

askButton.addEventListener("click", askQuestion);

insufficientButton.addEventListener("click", () => {
  queryInput.value = "What will be on my final exam?";
  topKInput.value = "3";
  minSimilarityInput.value = "0.75";
  askQuestion();
});
