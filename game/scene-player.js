// Renders Chapter 1 scenes into a container. `renderScenarioScene` and
// `renderQuizScene` are generic and reusable by any future chapter; the two
// animation scenes are custom per concept, dispatched by scene id.

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderAcidTestScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-4', scene.intro));
  if (scene.simulationNote) {
    container.appendChild(el('p', 'text-xs text-gray-500 italic mb-6', scene.simulationNote));
  }

  const badgeRow = el('div', 'flex gap-2 mb-6');
  const letters = ['A', 'C', 'I', 'D'];
  const badges = {};
  letters.forEach((letter) => {
    const badge = el('span', 'px-3 py-1 rounded-full border border-gray-700 text-gray-500 text-sm font-bold', letter);
    badges[letter] = badge;
    badgeRow.appendChild(badge);
  });
  container.appendChild(badgeRow);

  const balancesRow = el('div', 'flex gap-6 mb-6');
  const boxA = el('div', 'flex-1 rounded-xl border border-gray-800 bg-gray-900/60 p-4 text-center');
  const boxB = el('div', 'flex-1 rounded-xl border border-gray-800 bg-gray-900/60 p-4 text-center');
  boxA.appendChild(el('div', 'text-xs text-gray-500 mb-1', 'Account A'));
  boxB.appendChild(el('div', 'text-xs text-gray-500 mb-1', 'Account B'));
  const balA = el('div', 'text-2xl font-bold text-white');
  const balB = el('div', 'text-2xl font-bold text-white');
  boxA.appendChild(balA);
  boxB.appendChild(balB);
  balancesRow.appendChild(boxA);
  balancesRow.appendChild(boxB);
  container.appendChild(balancesRow);

  const narration = el('p', 'text-gray-200 leading-relaxed mb-6 min-h-[4.5rem]');
  container.appendChild(narration);

  const controls = el('div', 'flex items-center gap-3');
  const crashBtn = el('button', 'px-4 py-2 rounded-lg border border-red-800/60 text-red-300 hover:bg-red-900/30 transition text-sm', 'Simulate a crash here');
  const nextBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm', 'Next');
  controls.appendChild(crashBtn);
  controls.appendChild(nextBtn);
  container.appendChild(controls);

  let stepIndex = 0;

  function paintBadges(activeLetter) {
    letters.forEach((letter) => {
      badges[letter].className = letter === activeLetter
        ? 'px-3 py-1 rounded-full border border-blue-500 bg-blue-600/20 text-blue-300 text-sm font-bold'
        : 'px-3 py-1 rounded-full border border-gray-700 text-gray-500 text-sm font-bold';
    });
  }

  function paintStep(step) {
    balA.textContent = `$${step.balances.a}`;
    balB.textContent = `$${step.balances.b}`;
    narration.textContent = step.narration;
    paintBadges(step.acidLetter);
    crashBtn.disabled = stepIndex !== scene.crashStep;
    crashBtn.classList.toggle('opacity-30', crashBtn.disabled);
    crashBtn.classList.toggle('cursor-not-allowed', crashBtn.disabled);
  }

  function finish() {
    controls.innerHTML = '';
    const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', `Finish scene (+${scene.xp} XP)`);
    done.addEventListener('click', () => onComplete(scene.xp));
    controls.appendChild(done);
  }

  crashBtn.addEventListener('click', () => {
    if (stepIndex !== scene.crashStep) return;
    narration.textContent = scene.crashNarration;
    balA.textContent = `$${scene.steps[0].balances.a}`;
    balB.textContent = `$${scene.steps[0].balances.b}`;
    paintBadges('A');
    finish();
  });

  nextBtn.addEventListener('click', () => {
    stepIndex += 1;
    if (stepIndex >= scene.steps.length) {
      finish();
      return;
    }
    paintStep(scene.steps[stepIndex]);
  });

  paintStep(scene.steps[0]);
}

function renderTwoPathsScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-6', scene.intro));

  const grid = el('div', 'grid grid-cols-2 gap-6 mb-6');
  const detail = el('p', 'text-gray-200 leading-relaxed mb-6 min-h-[3rem]', 'Click any marker to reveal what it means.');
  const viewed = new Set();
  const totalMarkers = scene.columns.reduce((sum, c) => sum + c.markers.length, 0);

  const controls = el('div', 'flex items-center gap-3');

  function maybeShowContinue() {
    if (viewed.size < totalMarkers || controls.dataset.shown) return;
    controls.dataset.shown = '1';
    const continueBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm', 'Continue');
    continueBtn.addEventListener('click', () => {
      container.innerHTML = '';
      container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-4', scene.sharedGround));
      container.appendChild(el('p', 'text-gray-200 leading-relaxed mb-6', scene.closingNarration));
      const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', `Finish scene (+${scene.xp} XP)`);
      done.addEventListener('click', () => onComplete(scene.xp));
      container.appendChild(done);
    });
    controls.appendChild(continueBtn);
  }

  scene.columns.forEach((col) => {
    const colEl = el('div', '');
    colEl.appendChild(el('h4', `text-sm font-bold mb-3 text-${col.color}-300`, col.name));
    col.markers.forEach((marker) => {
      const btn = el('button', 'block w-full text-left px-3 py-2 mb-2 rounded-lg border border-gray-800 bg-gray-900/40 hover:bg-gray-800/60 transition text-sm text-gray-300');
      btn.appendChild(el('span', 'text-xs text-gray-500 mr-2', marker.year));
      btn.appendChild(document.createTextNode(marker.label));
      btn.addEventListener('click', () => {
        detail.textContent = marker.detail;
        viewed.add(col.key + ':' + marker.label);
        maybeShowContinue();
      });
      colEl.appendChild(btn);
    });
    grid.appendChild(colEl);
  });

  container.appendChild(grid);
  container.appendChild(detail);
  container.appendChild(controls);
}

function renderScenarioScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-6', scene.intro));

  const body = el('div');
  container.appendChild(body);

  let vignetteIndex = 0;
  let earnedXp = 0;

  function paintVignette() {
    body.innerHTML = '';
    const vignette = scene.vignettes[vignetteIndex];
    body.appendChild(el('div', 'text-xs uppercase tracking-wide text-blue-400 mb-2', vignette.category));
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', vignette.prompt));

    const optionsWrap = el('div', 'space-y-2 mb-4');
    const feedback = el('p', 'text-gray-300 leading-relaxed mb-4 hidden');
    const nextBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm hidden',
      vignetteIndex === scene.vignettes.length - 1 ? 'See results' : 'Next situation');

    vignette.options.forEach((option) => {
      const btn = el('button', 'block w-full text-left px-4 py-3 rounded-lg border border-gray-800 bg-gray-900/40 hover:bg-gray-800/60 transition text-sm text-gray-300', option.text);
      btn.addEventListener('click', () => {
        Array.from(optionsWrap.children).forEach((c) => (c.disabled = true));
        btn.className = option.correct
          ? 'block w-full text-left px-4 py-3 rounded-lg border border-emerald-600 bg-emerald-900/30 text-emerald-200 text-sm'
          : 'block w-full text-left px-4 py-3 rounded-lg border border-red-800 bg-red-900/20 text-red-200 text-sm';
        earnedXp += option.correct ? 6 : 2;
        feedback.textContent = option.feedback;
        feedback.classList.remove('hidden');
        nextBtn.classList.remove('hidden');
      });
      optionsWrap.appendChild(btn);
    });

    body.appendChild(optionsWrap);
    body.appendChild(feedback);

    nextBtn.addEventListener('click', () => {
      vignetteIndex += 1;
      if (vignetteIndex >= scene.vignettes.length) finish();
      else paintVignette();
    });
    body.appendChild(nextBtn);
  }

  function finish() {
    body.innerHTML = '';
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', `You earned ${earnedXp} XP across ${scene.vignettes.length} situations.`));
    const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', 'Finish scene');
    done.addEventListener('click', () => onComplete(earnedXp));
    body.appendChild(done);
  }

  paintVignette();
}

function renderQuizScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-6', scene.intro));

  const body = el('div');
  container.appendChild(body);

  let qIndex = 0;
  let correctCount = 0;

  function paintQuestion() {
    body.innerHTML = '';
    const q = scene.questions[qIndex];
    body.appendChild(el('div', 'text-xs text-gray-500 mb-2', `Question ${qIndex + 1} of ${scene.questions.length}`));
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', q.prompt));

    const choicesWrap = el('div', 'space-y-2 mb-4');
    const explanation = el('p', 'text-gray-300 leading-relaxed mb-4 hidden');
    const nextBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm hidden',
      qIndex === scene.questions.length - 1 ? 'See results' : 'Next question');

    q.choices.forEach((choiceText, i) => {
      const btn = el('button', 'block w-full text-left px-4 py-3 rounded-lg border border-gray-800 bg-gray-900/40 hover:bg-gray-800/60 transition text-sm text-gray-300', choiceText);
      btn.addEventListener('click', () => {
        Array.from(choicesWrap.children).forEach((c) => (c.disabled = true));
        const isCorrect = i === q.correctIndex;
        btn.className = isCorrect
          ? 'block w-full text-left px-4 py-3 rounded-lg border border-emerald-600 bg-emerald-900/30 text-emerald-200 text-sm'
          : 'block w-full text-left px-4 py-3 rounded-lg border border-red-800 bg-red-900/20 text-red-200 text-sm';
        if (isCorrect) correctCount += 1;
        else {
          choicesWrap.children[q.correctIndex].className = 'block w-full text-left px-4 py-3 rounded-lg border border-emerald-600 bg-emerald-900/30 text-emerald-200 text-sm';
        }
        explanation.textContent = q.explanation;
        explanation.classList.remove('hidden');
        nextBtn.classList.remove('hidden');
      });
      choicesWrap.appendChild(btn);
    });

    body.appendChild(choicesWrap);
    body.appendChild(explanation);

    nextBtn.addEventListener('click', () => {
      qIndex += 1;
      if (qIndex >= scene.questions.length) finish();
      else paintQuestion();
    });
    body.appendChild(nextBtn);
  }

  function finish() {
    body.innerHTML = '';
    const xp = correctCount * scene.xpPerCorrect;
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', `You got ${correctCount} of ${scene.questions.length} correct (+${xp} XP).`));
    const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', 'Finish scene');
    done.addEventListener('click', () => onComplete(xp));
    body.appendChild(done);
  }

  paintQuestion();
}

const ANIMATION_RENDERERS = {
  'acid-test': renderAcidTestScene,
  'two-paths': renderTwoPathsScene,
};

export function renderScene(container, scene, onComplete) {
  if (scene.type === 'animation') {
    const renderer = ANIMATION_RENDERERS[scene.id];
    if (!renderer) throw new Error(`No animation renderer registered for scene id "${scene.id}"`);
    renderer(container, scene, onComplete);
  } else if (scene.type === 'scenario') {
    renderScenarioScene(container, scene, onComplete);
  } else if (scene.type === 'quiz') {
    renderQuizScene(container, scene, onComplete);
  } else {
    throw new Error(`Unknown scene type "${scene.type}"`);
  }
}

export function mountChapterGame(root, { chapterId, scenes, store }) {
  root.innerHTML = '';

  const header = el('div', 'flex items-center justify-between mb-8');
  const xpLabel = el('div', 'text-sm text-gray-400');
  const chapterLabel = el('div', 'text-sm text-gray-400');
  header.appendChild(xpLabel);
  header.appendChild(chapterLabel);
  root.appendChild(header);

  const nav = el('div', 'flex gap-2 mb-8 flex-wrap');
  root.appendChild(nav);

  const sceneContainer = el('div', 'rounded-2xl border border-gray-800 bg-gray-900/40 p-6');
  root.appendChild(sceneContainer);

  function navButtonClass(scene, isActive) {
    if (isActive) return 'px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium';
    return store.isSceneComplete(chapterId, scene.id)
      ? 'px-3 py-1.5 rounded-lg bg-gray-800 text-emerald-300 text-xs font-medium'
      : 'px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 text-xs font-medium hover:text-white transition';
  }

  function refreshHeader() {
    xpLabel.textContent = `⚡ ${store.getTotalXp()} XP`;
    const stats = store.getChapterStats(chapterId, scenes.length);
    chapterLabel.textContent = stats.mastered
      ? 'Chapter mastered ✓'
      : `${stats.completedScenes} / ${stats.totalScenes} scenes complete`;
  }

  function selectScene(scene) {
    Array.from(nav.children).forEach((btn) => {
      btn.className = navButtonClass(scene, btn.dataset.sceneId === scene.id);
    });
    renderScene(sceneContainer, scene, (xp) => {
      store.awardSceneXp(chapterId, scene.id, xp);
      refreshHeader();
      const navBtn = Array.from(nav.children).find((btn) => btn.dataset.sceneId === scene.id);
      if (navBtn) navBtn.className = 'px-3 py-1.5 rounded-lg bg-gray-800 text-emerald-300 text-xs font-medium';
    });
  }

  scenes.forEach((scene) => {
    const btn = el('button', navButtonClass(scene, false), scene.title);
    btn.dataset.sceneId = scene.id;
    btn.addEventListener('click', () => selectScene(scene));
    nav.appendChild(btn);
  });

  refreshHeader();
  selectScene(scenes[0]);
}
