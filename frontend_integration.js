/* Connects the existing AI Study Buddy page to the local Python API. */
(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const byId = (id) => document.getElementById(id);
  let pendingApprovalId = null;
  let serverStatus = "Checking server…";

  function findInput() {
    return byId("user-input") ||
           $("textarea") ||
           $('input[type="text"]') ||
           $("input:not([type])");
}
  function findChatContainer() {
    return byId("chat-feed") ||
           byId("chatFeed") ||
           byId("chatMessages") ||
           $(".chat-feed") ||
           $(".chat-messages") ||
           $('[data-chat-messages]');


   }

  function addMessage(role, text) {
    const container = findChatContainer();
    if (!container) return;
    const item = document.createElement("div");
    item.className = role === "user"
      ? "my-3 ml-auto max-w-[85%] rounded-3xl bg-gradient-to-r from-amber-400 to-sun-500 px-5 py-3.5 text-slate-900 font-semibold shadow-sm border border-amber-500"
      : "my-3 mr-auto max-w-[92%] whitespace-pre-wrap rounded-3xl bg-white px-5 py-4 text-slate-800 border-2 border-campus-border shadow-sm text-sm leading-relaxed font-sans";
    item.textContent = text;
    container.appendChild(item);
    container.scrollTop = container.scrollHeight;
  }


  function updateRoadmapUI(plan) {
    if (!plan) return;
    const container = byId("plan-steps-container");
    const statusBadge = byId("plan-status-badge");
    if (!container) return;

    const steps = Array.isArray(plan) ? plan : (plan.steps || []);
    if (!steps.length) return;

    container.innerHTML = "";
    steps.forEach((step, idx) => {
      const desc = typeof step === "string" ? step : (step.description || "Step");
      const tool = typeof step === "object" ? (step.expected_tool || "none") : "none";
      const status = typeof step === "object" ? (step.status || "PENDING") : "PENDING";

      let statusColor = "bg-slate-100 text-slate-500 border-slate-200";
      let borderColor = "border-campus-border bg-campus-cream";
      let numColor = "bg-slate-200 text-slate-700";

      if (status.includes("COMPLETED")) {
        statusColor = "bg-emerald-100 text-emerald-800 border-emerald-300 font-bold";
        borderColor = "border-emerald-200 bg-emerald-50/50";
        numColor = "bg-emerald-500 text-white";
      } else if (status.includes("IN_PROGRESS")) {
        statusColor = "bg-amber-100 text-amber-800 border-amber-300 font-bold animate-pulse";
        borderColor = "border-amber-300 bg-amber-50/60";
        numColor = "bg-amber-500 text-white";
      } else if (status.includes("FAILED")) {
        statusColor = "bg-rose-100 text-rose-700 border-rose-300 font-bold";
        borderColor = "border-rose-200 bg-rose-50/50";
        numColor = "bg-rose-500 text-white";
      }

      const card = document.createElement("div");
      card.className = `p-3 rounded-2xl ${borderColor} border flex items-center gap-3 transition-all`;
      card.innerHTML = `
        <span class="w-6 h-6 rounded-full ${numColor} flex items-center justify-center font-bold text-xs shrink-0">${idx + 1}</span>
        <div class="flex-1 min-w-0">
          <div class="font-bold text-slate-800 truncate">${desc}</div>
          <div class="text-[11px] text-slate-400 font-mono">${tool}</div>
        </div>
        <span class="text-[10px] px-2 py-0.5 rounded-full border ${statusColor} shrink-0">${status}</span>
      `;
      container.appendChild(card);
    });

    if (statusBadge && plan.progress) {
      statusBadge.textContent = `${plan.progress.completed_steps}/${plan.progress.total_steps} (${plan.progress.percentage}%)`;
      statusBadge.className = plan.progress.percentage === 100
        ? "px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-mint-100 text-mint-700 border border-mint-200"
        : "px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-amber-100 text-amber-800 border border-amber-200";
    }
  }

function formatResult(result) {
  if (result.plan) {
    updateRoadmapUI(result.plan);
  }
  let output = "";

  // Display the action plan, whether it is an array or an object.
  const planSteps = Array.isArray(result.plan)
    ? result.plan
    : Array.isArray(result.plan?.steps)
      ? result.plan.steps
      : [];

  if (planSteps.length) {
    output += "ACTION PLAN\n";

    planSteps.forEach((step, index) => {
      const description = typeof step === "string"
        ? step
        : step.description || step.action || step.title || "Plan step";

      const status = typeof step === "object"
        ? step.status || "PENDING"
        : "PENDING";

      output += `${index + 1}. ${description} — ${status}\n`;
    });

    output += "\n";
  }

  // Display plan progress.
  const progress = result.plan?.progress;

  if (progress) {
    output += `Plan progress: ${progress.completed_steps}/${progress.total_steps} steps (${progress.percentage}%)\n\n`;
  }

  // Display tools used.
  if (result.tools_used?.length) {
    output += `Tools used: ${result.tools_used.join(", ")}\n\n`;
  }

  // Explain that this is the number of ReAct iterations.
  if (result.total_steps !== undefined) {
    output += `ReAct tool iterations: ${result.total_steps}\n\n`;
  }

  // Display the final answer.
  output += result.final_answer || result.answer || "The agent completed the task.";

  return output;
}


  async function postJson(url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok && response.status !== 202) {
      throw new Error(data.error || `Request failed (${response.status}).`);
    }
    return { status: response.status, data };
  }

  function showApproval(data) {
    pendingApprovalId = data.request_id;
    const modal = byId("safetyModal") || $(".safety-modal") || $('[role="dialog"]');
    const message = modal?.querySelector("[data-approval-message], .modal-message, p");
    if (message) {
      message.textContent =
        `The agent wants to run "${data.tool_name}" with these arguments:\n${JSON.stringify(data.args, null, 2)}\n\nAllow this action?`;
    }
    if (modal) {
      modal.classList.remove("hidden");
      modal.style.display = "block";
    } else {
      const allow = window.confirm(
        `The agent wants to run "${data.tool_name}".\n${JSON.stringify(data.args, null, 2)}\n\nAllow?`
      );
      respondSafety(allow);
    }
  }

  function closeApproval() {
    const modal = byId("safetyModal") || $(".safety-modal") || $('[role="dialog"]');
    if (modal) {
      modal.classList.add("hidden");
      modal.style.display = "none";
    }
  }

  async function askAgent(task) {
    const cleanTask = String(task || "").trim();
    if (!cleanTask) return;
    addMessage("user", cleanTask);
    try {
      const { status, data } = await postJson("/api/ask", { task: cleanTask });
      if (status === 202 || data.approval_required) {
        showApproval(data);
      } else if (data.result) {
        addMessage("assistant", formatResult(data.result));
      }
    } catch (error) {
      addMessage("assistant", `Error: ${error.message}`);
    }
  }

  async function respondSafety(approved) {
    if (!pendingApprovalId) {
      closeApproval();
      return;
    }
    const requestId = pendingApprovalId;
    pendingApprovalId = null;
    closeApproval();
    try {
      const { status, data } = await postJson("/api/approve", {
        request_id: requestId,
        approved: Boolean(approved),
      });
      if (data.cancelled) {
        addMessage("assistant", data.message || "Action cancelled.");
      } else if (status === 202 || data.approval_required) {
        showApproval(data);
      } else if (data.result) {
        addMessage("assistant", formatResult(data.result));
      }
    } catch (error) {
      addMessage("assistant", `Approval error: ${error.message}`);
    }
  }

  async function handleUserSubmit(event) {
    if (event) event.preventDefault();
    const input = findInput();
    if (!input) {
      addMessage("assistant", "I couldn't find the question input on this page.");
      return;
    }
    const task = input.value;
    input.value = "";
    await askAgent(task);
  }

  function runScenario(topic) {
    const prompts = {
      photosynthesis: "Explain photosynthesis in simple words and give an example.",
      error_recovery: "Explain how to recover from a mistake while studying, with a practical example.",
      gravity_notes: "Explain gravity and create concise study notes about it.",
    };
    askAgent(prompts[topic] || `Help me study ${topic}.`);
  }

  async function checkHealth() {
    try {
      const response = await fetch("/api/health", { cache: "no-store" });
      const data = await response.json();
      serverStatus = data.ok
        ? `Connected to ${data.fake_llm ? "fake/demo" : data.provider} AI`
        : "Server unavailable";
    } catch {
      serverStatus = "Python server is not reachable";
    }
    const statusNode = byId("engineStatus") || byId("engineLabel") || $("[data-engine-status]");
    if (statusNode) statusNode.textContent = serverStatus;

    const buttonLabel = byId("engine-label");
    if (buttonLabel) {
      buttonLabel.textContent = serverStatus.includes("fake/demo")
        ? "Tier 1: Fake LLM (Offline Test)"
        : serverStatus.startsWith("Connected to ")
          ? `Real LLM (${serverStatus.replace("Connected to ", "").replace(" AI", "")})`
          : "Server unavailable";
    }
  }

  function toggleEngineMode() {
    window.alert("The AI engine mode is controlled by config.py. " + serverStatus);
  }

  async function loadMemory() {
    try {
      const response = await fetch("/api/memory", { cache: "no-store" });
      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error("Could not load memory.");
      }

      const memory = data.memory || {};
      const profile = memory.user_profile || {};

      const mastered = byId("memory-mastered-list");
      const weak = byId("memory-weak-list");
      const history = byId("memory-history-list");

      if (mastered) {
        mastered.textContent = "";
        (memory.mastered_concepts || []).forEach(topic => {
          const item = document.createElement("span");
          item.className = "inline-block px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md";
          item.textContent = topic;
          mastered.appendChild(item);
        });
        if (!mastered.children.length) mastered.textContent = "No mastered topics yet.";
      }

      if (weak) {
        weak.textContent = "";
        (memory.weak_areas || []).forEach(topic => {
          const item = document.createElement("span");
          item.className = "inline-block px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-md";
          item.textContent = topic;
          weak.appendChild(item);
        });
        if (!weak.children.length) weak.textContent = "No topics to review yet.";
      }

      if (history) {
        history.textContent = "";
        (memory.task_history || []).slice(-5).reverse().forEach(task => {
          const item = document.createElement("div");
          item.className = "p-2 rounded bg-slate-50 border border-slate-100";
          item.textContent = task.summary || task.task || "Completed task";
          history.appendChild(item);
        });
        if (!history.children.length) history.textContent = "No task history yet.";
      }

      const profileBox = document.querySelector("#memory-drawer .bg-slate-50");
      if (profileBox) {
        profileBox.textContent = "";

        const grade = document.createElement("div");
        grade.textContent = "Grade: " + (profile.grade_level || "Not set");

        const preference = document.createElement("div");
        preference.textContent = "Preference: " + (profile.learning_style || "Not set");

        profileBox.append(grade, preference);
      }

    } catch (error) {
      console.error("Memory loading failed:", error);
    }
  }

  function toggleMemoryDrawer() {
    const drawer = byId("memory-drawer");
    if (!drawer) return;

    drawer.classList.toggle("translate-x-full");

    if (!drawer.classList.contains("translate-x-full")) {
      loadMemory();
    }
  }

  function toggleLogDrawer() {
    const drawer = byId("logDrawer") || byId("auditDrawer");
    if (drawer) drawer.classList.toggle("hidden");
    else window.alert("The server audit log is stored in logs/agent_audit.log.");
  }

  window.handleUserSubmit = handleUserSubmit;
  window.askAgent = askAgent;
  window.respondSafety = respondSafety;
  window.runScenario = runScenario;
  window.toggleEngineMode = toggleEngineMode;
  window.toggleMemoryDrawer = toggleMemoryDrawer;
  window.toggleLogDrawer = toggleLogDrawer;

  document.addEventListener("DOMContentLoaded", () => {
    const form = $("form");
    if (form && !form.dataset.agentConnected) {
      form.dataset.agentConnected = "true";
      form.addEventListener("submit", handleUserSubmit);
    }
    checkHealth();
    if (window.lucide?.createIcons) window.lucide.createIcons();
  });
})();
