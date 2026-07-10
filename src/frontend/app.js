const queryInput = document.getElementById("queryInput");
const responseModeInput = document.getElementById("responseModeInput");
const hintLevelInput = document.getElementById("hintLevelInput");
const topKInput = document.getElementById("topKInput");
const minSimilarityInput = document.getElementById("minSimilarityInput");
const askButton = document.getElementById("askButton");
const hintButton = document.getElementById("hintButton");
const insufficientButton = document.getElementById("insufficientButton");
const statusMessage = document.getElementById("statusMessage");
const resultPanel = document.getElementById("resultPanel");
const answerStatus = document.getElementById("answerStatus");
const answerText = document.getElementById("answerText");
const sourcesList = document.getElementById("sourcesList");


function setLoading(isLoading) {
  askButton.disabled = isLoading;
  hintButton.disabled = isLoading;
  insufficientButton.disabled = isLoading;

  statusMessage.textContent = isLoading
    ? "Generating a source-grounded response..."
    : "";
}


function updateHintLevelState() {
  hintLevelInput.disabled =
    responseModeInput.value === "answer";
}


function buildAskPayload() {
  const payload = {
    query: queryInput.value.trim(),
    top_k: Number.parseInt(topKInput.value, 10) || 3,
    response_mode: responseModeInput.value,
    hint_level:
      Number.parseInt(hintLevelInput.value, 10) || 1,
  };

  const minSimilarityValue =
    minSimilarityInput.value.trim();

  if (minSimilarityValue !== "") {
    payload.min_similarity_score =
      Number.parseFloat(minSimilarityValue);
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
      container.appendChild(
        document.createTextNode(part)
      );
    }
  }
}


function renderSources(sources) {
  sourcesList.textContent = "";

  if (!sources || sources.length === 0) {
    const emptyMessage =
      document.createElement("p");

    emptyMessage.className = "source-meta";
    emptyMessage.textContent =
      "No source evidence was returned for this response.";

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
    sourceId.textContent =
      source.source_id || "Source";

    const fileName = document.createElement("span");
    fileName.textContent =
      source.source || "Unknown source";

    title.appendChild(sourceId);
    title.appendChild(fileName);

    const chunkId = document.createElement("p");
    chunkId.className = "source-meta";
    chunkId.textContent =
      `Chunk: ${source.chunk_id || "N/A"}`;

    const similarity =
      document.createElement("p");

    similarity.className = "source-meta";

    if (
      typeof source.similarity_score === "number"
    ) {
      similarity.textContent =
        `Similarity score: ${
          source.similarity_score.toFixed(4)
        }`;
    } else {
      similarity.textContent =
        "Similarity score: N/A";
    }

    const preview =
      document.createElement("p");

    preview.className = "source-preview";
    preview.textContent =
      source.text_preview || "No preview available.";

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

  answerStatus.classList.remove(
    "insufficient",
    "hint",
    "out-of-scope"
  );

  if (data.answer_status === "insufficient_evidence") {
    answerStatus.classList.add("insufficient");
  } else if (data.answer_status === "hint") {
    answerStatus.classList.add("hint");
  } else if (data.answer_status === "out_of_scope") {
    answerStatus.classList.add("out-of-scope");
  }

  renderAnswerWithCitations(
    answerText,
    data.answer
  );

  renderSources(data.sources);
}


async function askQuestion() {
  const payload = buildAskPayload();

  if (!payload.query) {
    statusMessage.textContent =
      "Please enter a programming question.";
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
    statusMessage.textContent =
      `Request failed: ${error.message}`;
  } finally {
    setLoading(false);
  }
}


responseModeInput.addEventListener(
  "change",
  updateHintLevelState
);


askButton.addEventListener(
  "click",
  askQuestion
);


hintButton.addEventListener("click", () => {
  queryInput.value = (
    "I need help writing a loop to calculate the sum "
    + "of numbers in a list, but do not give me the "
    + "full answer immediately."
  );

  responseModeInput.value = "hint";
  hintLevelInput.value = "1";
  topKInput.value = "3";
  minSimilarityInput.value = "0.35";

  updateHintLevelState();
  askQuestion();
});


insufficientButton.addEventListener("click", () => {
  queryInput.value =
    "What will be on my final programming exam?";

  responseModeInput.value = "auto";
  hintLevelInput.value = "1";
  topKInput.value = "3";
  minSimilarityInput.value = "0.75";

  updateHintLevelState();
  askQuestion();
});


updateHintLevelState();
