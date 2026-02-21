/**
 * Main SPA router and page logic
 * Modern UI with card-based layout
 */
(function () {
  if (!localStorage.getItem('token')) {
    window.location.href = '/login';
    return;
  }

  let user = null;

  function setActiveNav() {
    const path = window.location.pathname.replace(/\/$/, '') || '/dashboard';
    const basePath = path.startsWith('/lesson/') ? '/lessons' : path;
    document.querySelectorAll('#mainNav a[href]').forEach((a) => {
      const href = a.getAttribute('href');
      a.classList.toggle('active', !!(href && href !== '#' && href === basePath));
    });
  }

  async function loadUser() {
    try {
      user = await api.users.me();
      document.getElementById('userInfo').textContent = user.full_name + ' (' + user.role + ')';
      const adminLink = document.querySelector('nav a[href="/admin"]');
      if (adminLink && (user.role === 'teacher' || user.role === 'admin')) {
        adminLink.style.display = '';
      } else if (adminLink) {
        adminLink.style.display = 'none';
      }
    } catch (e) {
      if (e.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
  }

  document.getElementById('logoutBtn').onclick = (e) => {
    e.preventDefault();
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  const routes = {
    '/dashboard': renderDashboard,
    '/lessons': renderLessons,
    '/exercises': renderExercises,
    '/tests': renderTests,
    '/chat': renderChat,
    '/vocabulary': renderVocabulary,
    '/progress': renderProgress,
    '/admin': renderAdmin,
  };

  function getPath() {
    return window.location.pathname.replace(/\/$/, '') || '/dashboard';
  }

  async function init() {
    const content = document.getElementById('content');
    if (!content) return;
    content.innerHTML = '<div class="loading">Загрузка...</div>';
    try {
      await loadUser();
      setActiveNav();
      const path = getPath();
      const fn = routes[path] || renderDashboard;
      await fn(content);
    } catch (e) {
      var errMsg = (e && (e.message || e.detail || e)) ? String(e.message || e.detail || e) : 'Неизвестная ошибка';
      if (e && e.data && typeof e.data.detail === 'string') errMsg = e.data.detail;
      content.innerHTML = '<div class="card"><div class="error">Ошибка загрузки: ' + (errMsg.replace(/</g, '&lt;')) + '</div><p style="margin-top:1rem;">Проверьте, что сервер запущен (например, <code>uvicorn main:app</code>).</p></div>';
    }
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function formatLessonContent(text) {
    if (!text) return '';
    return escapeHtml(text)
      .replace(/## ([^\n]+)/g, '<h4 style="margin: 1rem 0 0.5rem 0; color: #334155;">$1</h4>')
      .replace(/\n/g, '<br>');
  }

  // Dashboard
  async function renderDashboard(el) {
    const prog = await api.progress.summary();
    const acc = prog.exercise_attempts
      ? Math.round((prog.exercise_correct / prog.exercise_attempts) * 100)
      : 0;
    el.innerHTML = `
      <h1 class="page-title">Добро пожаловать</h1>
      <div class="card welcome-section">
        <h2>${escapeHtml(user.full_name)}</h2>
        <p>Виртуальный помощник для интерактивного изучения казахского языка. Продолжайте обучение или начните новый урок.</p>
      </div>
      <h3 style="margin: 0 0 1rem 0; font-size: 1rem; color: #64748b;">Ваш прогресс</h3>
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-value">${prog.completed_lessons} / ${prog.total_lessons}</div>
          <div class="stat-label">Уроков пройдено</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${acc}%</div>
          <div class="stat-label">Точность упражнений</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${prog.test_passed} / ${prog.test_attempts}</div>
          <div class="stat-label">Тестов сдано</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${prog.vocabulary_learned} / ${prog.vocabulary_size}</div>
          <div class="stat-label">Слов изучено</div>
        </div>
      </div>
      <div class="card">
        <h2>Быстрые действия</h2>
        <div class="quick-actions">
          <a href="/lessons" class="quick-action-btn"><span class="qa-icon">📚</span> Уроки</a>
          <a href="/exercises" class="quick-action-btn"><span class="qa-icon">✏️</span> Упражнения</a>
          <a href="/chat" class="quick-action-btn"><span class="qa-icon">💬</span> Помощник</a>
          <a href="/vocabulary" class="quick-action-btn"><span class="qa-icon">📖</span> Словарь</a>
        </div>
      </div>
    `;
  }

  // Lessons
  async function renderLessons(el) {
    const lessons = await api.lessons.list();
    const lessonCards = lessons.length
      ? lessons.map((l) => `
        <div class="lesson-card ${l.is_locked ? 'locked' : ''}">
          <div class="lesson-card-icon">📖</div>
          <div class="lesson-card-body">
            <span class="badge badge-level">${escapeHtml(l.level)}</span>
            <h3>${escapeHtml(l.title)}</h3>
            <p class="lesson-card-topic">${escapeHtml(l.topic)}</p>
            ${l.is_locked
              ? '<span class="lesson-card-locked">Завершите предыдущие уроки</span>'
              : '<a href="/lesson/' + l.id + '" class="btn lesson-card-btn">Открыть урок →</a>'}
          </div>
        </div>
      `).join('')
      : '<div class="empty-state empty-state-full"><div class="empty-state-icon">📚</div><p>Нет доступных уроков</p></div>';
    el.innerHTML = `
      <h1 class="page-title">Уроки</h1>
      <div class="lesson-cards-grid">${lessonCards}</div>
    `;
    el.querySelectorAll('a[href^="/lesson/"]').forEach((a) => {
      a.onclick = (e) => {
        e.preventDefault();
        showLesson(parseInt(a.href.split('/').pop()));
      };
    });
  }

  function showLesson(id) {
    const content = document.getElementById('content');
    content.innerHTML = '<div class="loading">Загрузка урока...</div>';
    Promise.all([api.lessons.get(id), api.lessons.getNext(id)]).then(async ([lesson, nextInfo]) => {
      let finalTestHtml = '';
      try {
        const tests = await api.tests.list(id);
        const finalTest = tests.find((t) => t.is_final);
        if (finalTest) {
          finalTestHtml = `
            <div class="card" style="background: #f0fdf4; border-color: #22c55e; margin-top: 1rem;">
              <p style="margin: 0 0 0.5rem 0;"><strong>Итоговый тест обязателен для завершения урока.</strong></p>
              <p style="margin: 0 0 1rem 0; font-size: 0.9rem; color: #64748b;">Для завершения урока необходимо сдать итоговый тест (≥70%, 20 вопросов).</p>
              <button class="btn" id="finalTestBtn">Пройти итоговый тест</button>
            </div>`;
        }
      } catch (_) {}
      content.innerHTML = `
        <div class="card">
          <div style="margin-bottom: 1rem;">
            <a href="/lessons" class="btn btn-secondary">← Назад к списку</a>
          </div>
          <h2>${escapeHtml(lesson.title)}</h2>
          <p style="color: #64748b;">
            <span class="badge badge-level">${escapeHtml(lesson.level)}</span> ${escapeHtml(lesson.topic)}
          </p>
          <div class="lesson-content">${formatLessonContent(lesson.content)}</div>
          ${finalTestHtml}
          <div class="btn-group" style="margin-top: 1rem;">
            <button class="btn btn-success" id="completeBtn">Завершить урок</button>
            <a href="/chat?lesson_id=${lesson.id}" class="btn btn-secondary">Спросить помощника</a>
          </div>
          <div class="card" style="margin-top: 1rem; background: #f8fafc;">
            <h4 style="margin: 0 0 0.5rem 0;">Задать вопрос по уроку</h4>
            <p style="color: #64748b; font-size: 0.9rem; margin: 0 0 0.5rem 0;">Ответ помощника будет учитывать контент этого урока.</p>
            <form id="lessonChatForm" class="chat-input-wrap" style="margin-top: 0.5rem;">
              <input type="text" id="lessonChatInput" placeholder="Например: Объясни этот урок">
              <button type="submit" class="btn">Отправить</button>
            </form>
            <div id="lessonChatReply" style="margin-top: 0.75rem; display: none;"></div>
          </div>
          <div id="nextLessonBlock" style="margin-top: 1.5rem;"></div>
        </div>
      `;
      const finalTestBtn = document.getElementById('finalTestBtn');
      if (finalTestBtn) {
        const tests = await api.tests.list(id);
        const ft = tests.find((t) => t.is_final);
        if (ft) {
          finalTestBtn.onclick = async () => {
            const res = await api.tests.startAttempt(ft.id);
            await runTest(res.attempt_id, ft.id);
          };
        }
      }
      document.getElementById('completeBtn').onclick = async () => {
        try {
          await api.lessons.complete(id);
          document.getElementById('completeBtn').textContent = 'Завершено ✓';
          document.getElementById('completeBtn').classList.add('btn-secondary');
          document.getElementById('completeBtn').classList.remove('btn-success');
        } catch (err) {
          alert(err.data?.detail || err.message || 'Ошибка');
        }
      };

      const lessonChatForm = document.getElementById('lessonChatForm');
      const lessonChatInput = document.getElementById('lessonChatInput');
      const lessonChatReply = document.getElementById('lessonChatReply');
      if (lessonChatForm && lessonChatInput && lessonChatReply) {
        lessonChatForm.onsubmit = async (e) => {
          e.preventDefault();
          const text = lessonChatInput.value.trim();
          if (!text) return;
          lessonChatReply.style.display = 'block';
          lessonChatReply.innerHTML = '<div class="loading">Отправка...</div>';
          const ctx = getChatContext(id);
          try {
            const res = await api.assistant.chat(text, ctx);
            const html = '<strong>Помощник</strong> ' + escapeHtml(res.response || '').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
            lessonChatReply.innerHTML = '<div class="chat-bubble" style="background: #e2e8f0; padding: 0.75rem; border-radius: 8px;">' + html + '</div>';
          } catch (err) {
            lessonChatReply.innerHTML = '<div class="error">' + escapeHtml(err.data?.detail || err.message || 'Ошибка') + '</div>';
          }
        };
      }

      const nextBlock = document.getElementById('nextLessonBlock');
      if (nextInfo && nextInfo.next_lesson_id) {
        if (nextInfo.is_accessible) {
          nextBlock.innerHTML = '<a href="/lesson/' + nextInfo.next_lesson_id + '" class="btn">Следующий урок: ' + escapeHtml(nextInfo.title) + ' (' + escapeHtml(nextInfo.level) + ')</a>';
        } else {
          nextBlock.innerHTML = '<div class="card" style="background: #fef3c7; border-color: #f59e0b;"><p><strong>Следующий урок:</strong> ' + escapeHtml(nextInfo.title) + ' (' + escapeHtml(nextInfo.level) + ')</p><p style="color: #92400e; font-size: 0.9rem;">Заблокировано: ' + escapeHtml(nextInfo.locked_reason || 'Сначала пройдите предыдущие уроки') + '</p><button class="btn btn-secondary" disabled>Доступен после выполнения условий</button></div>';
        }
      } else {
        nextBlock.innerHTML = '<div class="card" style="background: #f0fdf4;"><p><strong>Вы завершили этот уровень!</strong></p><a href="/lessons" class="btn">Вернуться к списку уроков</a></div>';
      }
    }).catch((e) => {
      content.innerHTML = '<div class="card"><div class="error">' + escapeHtml(e.data?.detail || e.message) + '</div></div>';
    });
  }

  // Exercises
  async function renderExercises(el) {
    const lessons = await api.lessons.list();
    const lessonOpts = lessons.filter((l) => !l.is_locked).map((l) =>
      `<option value="${l.id}">${escapeHtml(l.title)}</option>`
    ).join('');
    el.innerHTML = `
      <h1 class="page-title">Упражнения</h1>
      <div class="card">
        <div class="form-group" style="max-width: 320px;">
          <label>Фильтр по уроку</label>
          <select id="lessonSelect"><option value="">Все уроки</option>${lessonOpts}</select>
        </div>
        <div id="exerciseList"></div>
      </div>
    `;
    const load = async () => {
      const lid = document.getElementById('lessonSelect').value;
      const ex = await api.exercises.list(lid || null);
      const list = document.getElementById('exerciseList');
      list.innerHTML = ex.length
        ? '<div class="exercise-list">' + ex.map((e) => `
          <a href="#" class="exercise-card" data-id="${e.id}">
            <strong>${escapeHtml(e.title)}</strong>
            <span class="badge badge-neutral" style="margin-left: 0.5rem;">${escapeHtml(e.exercise_type)}</span>
          </a>
        `).join('') + '</div>'
        : '<div class="empty-state"><div class="empty-state-icon">✏️</div><p>Нет упражнений для выбранного урока</p></div>';
      list.querySelectorAll('.exercise-card').forEach((a) => {
        a.onclick = (e) => {
          e.preventDefault();
          showExercise(parseInt(a.dataset.id));
        };
      });
    };
    document.getElementById('lessonSelect').onchange = load;
    load();
  }

  function showExercise(id) {
    const content = document.getElementById('content');
    content.innerHTML = '<div class="loading">Загрузка...</div>';
    api.exercises.get(id).then((ex) => {
      let formHtml = '';
      const c = ex.content || {};
      if (ex.exercise_type === 'multiple_choice') {
        const opts = (c.options || []).map((o) =>
          `<label class="exercise-option"><input type="radio" name="answer" value="${escapeHtml(o)}"> ${escapeHtml(o)}</label>`
        ).join('');
        formHtml = `<p style="font-weight: 500; margin-bottom: 1rem;">${escapeHtml(c.question || 'Выберите ответ')}</p><div class="exercise-options">${opts}</div>`;
      } else {
        formHtml = `<p style="font-weight: 500; margin-bottom: 1rem;">${escapeHtml(c.question || 'Введите ответ')}</p><input type="text" id="answer" placeholder="Ваш ответ">`;
      }
      content.innerHTML = `
        <div class="card">
          <div style="margin-bottom: 1rem;">
            <a href="/exercises" class="btn btn-secondary">← Назад</a>
          </div>
          <h2>${escapeHtml(ex.title)}</h2>
          <form id="exForm">
            ${formHtml}
            <div style="margin-top: 1.5rem;">
              <button type="submit" class="btn">Проверить</button>
            </div>
          </form>
          <div id="exResult" style="margin-top: 1rem;"></div>
        </div>
      `;
      document.getElementById('exForm').onsubmit = async (e) => {
        e.preventDefault();
        let ans;
        const r = document.querySelector('input[name="answer"]:checked');
        if (r) ans = r.value;
        else ans = document.getElementById('answer')?.value || '';
        try {
          const res = await api.exercises.submit(id, { answer: ans });
          document.getElementById('exResult').innerHTML = res.is_correct
            ? '<div class="success">Верно!</div>'
            : '<div class="error">Неверно. Попробуйте ещё раз.</div>';
        } catch (err) {
          document.getElementById('exResult').innerHTML = '<div class="error">' + escapeHtml(err.data?.detail || err.message) + '</div>';
        }
      };
    });
  }

  // Tests
  async function renderTests(el) {
    const tests = await api.tests.list();
    const testCards = tests.length
      ? tests.map((t) => `
        <div class="lesson-card">
          <div class="lesson-info">
            <h3>${escapeHtml(t.title)} ${t.is_final ? '<span class="badge badge-success" style="margin-left: 0.5rem;">Итоговый</span>' : ''}</h3>
          </div>
          <a href="#" class="btn" data-id="${t.id}">Пройти тест</a>
        </div>
      `).join('')
      : '<div class="empty-state"><div class="empty-state-icon">📝</div><p>Нет доступных тестов</p></div>';
    el.innerHTML = `
      <h1 class="page-title">Тесты</h1>
      <div class="card">
        <div class="lesson-list">${testCards}</div>
      </div>
    `;
    el.querySelectorAll('a[data-id]').forEach((a) => {
      a.onclick = async (e) => {
        e.preventDefault();
        const id = parseInt(a.dataset.id);
        const res = await api.tests.startAttempt(id);
        await runTest(res.attempt_id, id);
      };
    });
  }

  async function runTest(attemptId, testId) {
    const content = document.getElementById('content');
    const questions = await api.tests.getQuestions(testId);
    if (!questions.length) {
      content.innerHTML = '<div class="card"><div class="empty-state"><p>Нет вопросов в тесте.</p></div></div>';
      return;
    }
    let html = '<div class="card"><div style="margin-bottom: 1rem;"><a href="/tests" class="btn btn-secondary">← Назад</a></div><h2>Тест</h2><form id="testForm">';
    questions.forEach((q, i) => {
      const c = q.content || {};
      let inp = `<input type="text" name="q_${q.id}" placeholder="Введите ответ">`;
      if (c.options && c.options.length) {
        inp = '<div class="exercise-options">' + c.options.map((o) =>
          `<label class="exercise-option"><input type="radio" name="q_${q.id}" value="${escapeHtml(o)}"> ${escapeHtml(o)}</label>`
        ).join('') + '</div>';
      }
      html += `<div class="form-group"><p style="font-weight: 500;">${i + 1}. ${escapeHtml(q.question_text)}</p>${inp}</div>`;
    });
    html += '<button type="submit" class="btn">Отправить тест</button></form><div id="testResult" style="margin-top: 1rem;"></div></div>';
    content.innerHTML = html;
    document.getElementById('testForm').onsubmit = async (e) => {
      e.preventDefault();
      const form = e.target;
      const answers = questions.map((q) => {
        const el = form.elements['q_' + q.id];
        const val = el ? (el.type === 'radio' ? (form.querySelector('input[name="q_' + q.id + '"]:checked')?.value || '') : el.value) : '';
        return { question_id: q.id, user_answer: { answer: val } };
      });
      try {
        const res = await api.tests.submitAttempt(attemptId, answers);
        document.getElementById('testResult').innerHTML =
          '<div class="' + (res.passed ? 'success' : 'error') + '">Результат: ' + res.score + '%. ' + (res.passed ? 'Тест сдан!' : 'Для сдачи нужно ≥70%. Попробуйте ещё раз.') + '</div>' +
          (!res.passed ? '<p style="margin-top: 0.5rem;"><a href="/tests" class="btn btn-secondary">К списку тестов (пройти снова)</a></p>' : '');
      } catch (err) {
        document.getElementById('testResult').innerHTML = '<div class="error">' + escapeHtml(err.data?.detail || err.message) + '</div>';
      }
    };
  }

  // Chat — context.lesson_id and mode='lesson' when on /chat?lesson_id=X or when sending from /lesson/{id}
  function getChatContext(overrideLessonId) {
    const params = new URLSearchParams(window.location.search);
    const lessonId = overrideLessonId != null ? overrideLessonId : params.get('lesson_id');
    const lid = lessonId != null ? parseInt(lessonId, 10) : null;
    const ctx = {
      mode: lid ? 'lesson' : 'free',
      user_level: (user && user.language_level) ? user.language_level : 'A1',
    };
    if (lid) ctx.lesson_id = lid;
    return ctx;
  }

  async function renderChat(el) {
    if (!el) return;
    try {
      el.innerHTML = [
        '<h1 class="page-title">Виртуальный помощник</h1>',
        '<div class="card">',
        '<p style="color: #64748b; margin-bottom: 1rem;">Задайте вопрос о грамматике, приветствиях или правилах казахского языка.</p>',
        '<div class="chat-container">',
        '<div id="chatMessages" class="chat-messages"></div>',
        '<form id="chatForm" class="chat-input-wrap">',
        '<input type="text" id="chatInput" placeholder="Ваш вопрос...">',
        '<button type="submit" class="btn">Отправить</button>',
        '</form>',
        '</div>',
        '</div>'
      ].join('');
    } catch (e) {
      el.innerHTML = '<div class="card"><div class="error">Ошибка отображения чата.</div></div>';
      return;
    }
    const msgs = document.getElementById('chatMessages');
    const inp = document.getElementById('chatInput');
    const chatForm = document.getElementById('chatForm');
    if (!msgs || !inp || !chatForm) {
      el.innerHTML = '<div class="card"><div class="error">Ошибка: элементы чата не найдены.</div></div>';
      return;
    }

    async function sendMessage(msg, extraContext) {
      if (!msg || !msg.trim()) return;
      const text = msg.trim();
      msgs.innerHTML += '<div class="chat-message user"><div class="chat-bubble"><strong>Вы</strong> ' + escapeHtml(text) + '</div></div>';
      inp.value = '';
      msgs.scrollTop = msgs.scrollHeight;

      const ctx = { ...getChatContext(), ...(extraContext || {}) };
      console.log('[Assistant] request:', { message: text, context: ctx });

      try {
        const res = await api.assistant.chat(text, ctx);
        console.log('[Assistant] response:', { source: res.source, intent: res.source, mentioned_words: (res.mentioned_words || []).length });

        const sourceLabel = res.source === 'dictionary' ? 'словарь' : res.source === 'lesson' ? 'урок' : 'правило';
        let bubbleHtml = '<span class="chat-source-badge" title="Источник: ' + sourceLabel + '">' + escapeHtml(sourceLabel) + '</span> ';
        bubbleHtml += '<strong>Помощник</strong> ' + escapeHtml(res.response || '').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');

        const navBtns = res.nav_buttons || [];
        const quickRepl = res.quick_replies || [];
        const mentionedWords = res.mentioned_words || [];
        const allSuggestions = [...navBtns, ...quickRepl];

        if (allSuggestions.length || (res.last_topic != null || res.last_rule != null) || mentionedWords.length) {
          bubbleHtml += '<div class="chat-suggestions-wrap">';
          if (allSuggestions.length) {
            bubbleHtml += '<div class="chat-quick-replies"><span class="chat-suggestions-label">Спросить:</span> ';
            allSuggestions.forEach((s) => {
              bubbleHtml += '<button type="button" class="chat-suggestion chat-suggestion-quick" data-msg="' + escapeHtml(s).replace(/"/g, '&quot;') + '">' + escapeHtml(s) + '</button> ';
            });
            bubbleHtml += '</div>';
          }
          if (res.last_topic != null || res.last_rule != null) {
            bubbleHtml += '<div class="chat-quick-actions"><span class="chat-suggestions-label">Ответ:</span> ';
            bubbleHtml += '<button type="button" class="chat-suggestion chat-suggestion-refine" data-refine="simple">Проще</button> ';
            bubbleHtml += '<button type="button" class="chat-suggestion chat-suggestion-refine" data-refine="detailed">Подробнее</button> ';
            bubbleHtml += '<button type="button" class="chat-suggestion chat-suggestion-refine" data-refine="examples">Примеры</button></div>';
          }
          if (mentionedWords.length) {
            bubbleHtml += '<div class="chat-add-vocab"><span class="chat-suggestions-label">Словарь:</span> ';
            mentionedWords.forEach(function(m) {
              bubbleHtml += '<button type="button" class="chat-suggestion chat-add-vocab-btn" data-vocab-id="' + m.vocabulary_id + '" data-word="' + escapeHtml(m.word_kz) + '">Добавить в словарь: ' + escapeHtml(m.word_kz) + '</button> ';
            });
            bubbleHtml += '</div>';
          }
          bubbleHtml += '</div>';
        }

        const lastTopic = res.last_topic != null ? String(res.last_topic) : '';
        const lastRule = res.last_rule != null ? String(res.last_rule) : '';
        msgs.innerHTML += '<div class="chat-message assistant"><div class="chat-bubble" data-last-topic="' + escapeHtml(lastTopic) + '" data-last-rule="' + escapeHtml(lastRule) + '">' + bubbleHtml + '</div></div>';

        msgs.querySelectorAll('.chat-suggestion-quick').forEach((btn) => {
          btn.onclick = function() {
            const m = this.getAttribute('data-msg');
            if (m) sendMessage(m);
          };
        });
        msgs.querySelectorAll('.chat-suggestion-refine').forEach((btn) => {
          btn.onclick = function() {
            const bubble = this.closest('.chat-bubble');
            const refine = this.getAttribute('data-refine');
            const topic = bubble ? bubble.getAttribute('data-last-topic') : '';
            const rule = bubble ? bubble.getAttribute('data-last-rule') : '';
            const label = refine === 'simple' ? 'Проще' : refine === 'detailed' ? 'Подробнее' : 'Примеры';
            sendMessage(label, { refine_mode: refine, last_topic: topic || undefined, last_rule: rule || undefined });
          };
        });
        msgs.querySelectorAll('.chat-add-vocab-btn').forEach((btn) => {
          btn.onclick = async function() {
            const vid = this.getAttribute('data-vocab-id');
            if (!vid) return;
            try {
              await api.vocabulary.add({ vocabulary_id: parseInt(vid, 10) });
              this.textContent = 'Добавлено';
              this.disabled = true;
            } catch (e) {
              if (e.data && (e.data.detail || '').indexOf('already') >= 0) {
                this.textContent = 'Уже в словаре';
                this.disabled = true;
              } else {
                console.error(e);
              }
            }
          };
        });
      } catch (err) {
        let errMsg = err.message || 'Ошибка сети';
        if (err.data) {
          const d = err.data.detail;
          if (typeof d === 'string') errMsg = d;
          else if (Array.isArray(d) && d[0] && d[0].msg) errMsg = d.map((x) => x.msg).join('; ');
          else if (d) errMsg = JSON.stringify(d);
        }
        console.error('[Assistant] error:', err.status, errMsg);
        msgs.innerHTML += '<div class="chat-message assistant"><div class="chat-bubble"><strong>Ошибка</strong> ' + escapeHtml(String(errMsg)) + '</div></div>';
      }
      msgs.scrollTop = msgs.scrollHeight;
    }

    chatForm.onsubmit = async (e) => {
      e.preventDefault();
      await sendMessage(inp.value);
    };
  }

  // Vocabulary
  async function renderVocabulary(el) {
    const [learning, learned] = await Promise.all([
      api.vocabulary.list('in_progress'),
      api.vocabulary.list('learned'),
    ]);
    const learningRows = learning.map((v) => `
      <tr>
        <td><strong>${escapeHtml(v.word_kz)}</strong></td>
        <td>${escapeHtml(v.translation_ru)}</td>
        <td><div class="mastery-bar"><div class="mastery-fill" style="width: ${(v.mastery || 0) * 20}%"></div></div> ${v.mastery || 0}/5</td>
        <td class="table-actions">
          <button class="btn btn-danger btn-sm" data-action="remove" data-id="${v.id}">Удалить</button>
        </td>
      </tr>
    `).join('');
    const learnedRows = learned.map((v) => `
      <tr>
        <td><strong>${escapeHtml(v.word_kz)}</strong></td>
        <td>${escapeHtml(v.translation_ru)}</td>
        <td class="table-actions">
          <button class="btn btn-danger btn-sm" data-action="remove" data-id="${v.id}">Удалить</button>
        </td>
      </tr>
    `).join('');
    el.innerHTML = `
      <h1 class="page-title">Личный словарь</h1>
      <div class="card">
        <h2>Добавить слово</h2>
        <form id="addWordForm" class="vocab-form">
          <div class="form-group" style="margin-bottom: 0;">
            <label>Слово (казах.)</label>
            <input type="text" id="word_kz" placeholder="Например: сәлем" required>
          </div>
          <div class="form-group" style="margin-bottom: 0;">
            <label>Перевод</label>
            <input type="text" id="translation_ru" placeholder="Например: привет" required>
          </div>
          <button type="submit" class="btn">Добавить</button>
        </form>
      </div>
      <div class="card">
        <div class="vocab-tabs">
          <button type="button" class="vocab-tab active" data-tab="learning">Изучаю (${learning.length})</button>
          <button type="button" class="vocab-tab" data-tab="learned">Изучено (${learned.length})</button>
        </div>
        <div id="tabLearning" class="vocab-tab-content">
          <div style="margin-bottom: 1rem;">
            <button type="button" class="btn" id="startGameBtn">Начать игру</button>
          </div>
          <div id="gameArea" style="display: none;">
            <div class="game-prompt" id="gamePrompt"></div>
            <div id="gameInputArea"></div>
            <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
              <button type="button" class="btn" id="gameSubmitBtn">Проверить</button>
              <button type="button" class="btn btn-secondary" id="endGameBtn">Закончить игру</button>
            </div>
            <div id="gameFeedback" style="margin-top: 0.5rem;"></div>
          </div>
          <div id="vocabListInLearning">${learning.length ? '<div class="table-wrap"><table><thead><tr><th>Слово</th><th>Перевод</th><th>Мастерство</th><th></th></tr></thead><tbody>' + learningRows + '</tbody></table></div>' : '<div class="empty-state"><div class="empty-state-icon">📖</div><p>Нет слов для изучения. Добавьте слово выше.</p></div>'}</div>
        </div>
        <div id="tabLearned" class="vocab-tab-content" style="display: none;">
          ${learned.length ? '<div class="table-wrap"><table><thead><tr><th>Слово</th><th>Перевод</th><th></th></tr></thead><tbody>' + learnedRows + '</tbody></table></div>' : '<div class="empty-state"><p>Пока нет изученных слов.</p></div>'}
        </div>
      </div>
    `;
    document.getElementById('addWordForm').onsubmit = async (e) => {
      e.preventDefault();
      try {
        await api.vocabulary.add({
          word_kz: document.getElementById('word_kz').value,
          translation_ru: document.getElementById('translation_ru').value,
        });
        location.reload();
      } catch (err) {
        alert(err.data?.detail || err.message);
      }
    };
    el.querySelectorAll('[data-tab]').forEach((btn) => {
      btn.onclick = () => {
        el.querySelectorAll('.vocab-tab').forEach((t) => t.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tabLearning').style.display = btn.dataset.tab === 'learning' ? '' : 'none';
        document.getElementById('tabLearned').style.display = btn.dataset.tab === 'learned' ? '' : 'none';
      };
    });
    el.querySelectorAll('[data-action="remove"]').forEach((btn) => {
      btn.onclick = () => api.vocabulary.remove(btn.dataset.id).then(() => location.reload());
    });
    let currentQuestion = null;
    let lastVocabId = null;
    const startBtn = document.getElementById('startGameBtn');
    if (startBtn) startBtn.addEventListener('click', async () => {
      try {
        const res = await api.vocabulary.gameNext(lastVocabId);
        if (!res.question) {
          alert(res.message || 'Нет слов для изучения.');
          return;
        }
      currentQuestion = res.question;
      lastVocabId = currentQuestion.vocab_id;
      document.getElementById('gameArea').style.display = '';
      const vocabList = document.getElementById('vocabListInLearning');
      if (vocabList) vocabList.style.display = 'none';
      document.getElementById('gameFeedback').innerHTML = '';
      const q = currentQuestion;
      document.getElementById('gamePrompt').textContent = q.mode === 'reverse' ? 'Переведите на казахский: ' + q.prompt : 'Переведите на русский: ' + q.prompt;
      const inputArea = document.getElementById('gameInputArea');
      if (q.options && q.options.length) {
        inputArea.innerHTML = '<div class="exercise-options">' + q.options.map((o) =>
          '<label class="exercise-option"><input type="radio" name="gameAnswer" value="' + escapeHtml(o) + '"> ' + escapeHtml(o) + '</label>'
        ).join('') + '</div>';
      } else {
        inputArea.innerHTML = '<input type="text" id="gameAnswerInput" placeholder="Ваш ответ">';
      }
      } catch (err) {
        alert('Ошибка: ' + (err.data?.detail || err.message || 'Не удалось загрузить вопрос'));
      }
    });
    const endGameBtn = document.getElementById('endGameBtn');
    if (endGameBtn) endGameBtn.addEventListener('click', () => {
      currentQuestion = null;
      lastVocabId = null;
      document.getElementById('gameArea').style.display = 'none';
      const vl = document.getElementById('vocabListInLearning');
      if (vl) vl.style.display = '';
    });
    const gameSubmitBtn = document.getElementById('gameSubmitBtn');
    if (gameSubmitBtn) gameSubmitBtn.addEventListener('click', async () => {
      if (!currentQuestion) return;
      let val = '';
      const radio = document.querySelector('input[name="gameAnswer"]:checked');
      if (radio) val = radio.value;
      else val = (document.getElementById('gameAnswerInput') || {}).value || '';
      if (!val.trim()) { document.getElementById('gameFeedback').innerHTML = '<span class="error">Введите ответ</span>'; return; }
      try {
        const res = await api.vocabulary.gameAnswer(currentQuestion.vocab_id, currentQuestion.mode, val);
        const fb = document.getElementById('gameFeedback');
        fb.innerHTML = res.is_correct
          ? '<span class="success">✓ Правильно! Мастерство: ' + res.mastery + '/5' + (res.status === 'learned' ? ' — Слово изучено!' : '') + '</span>'
          : '<span class="error">✗ Неверно. Правильно: ' + escapeHtml(res.correct_answer || '') + '. Мастерство: ' + res.mastery + '/5</span>';
        if (res.status === 'learned') lastVocabId = null;
        setTimeout(async () => {
          const nextRes = await api.vocabulary.gameNext(lastVocabId);
          if (!nextRes.question) {
            fb.innerHTML += '<p style="margin-top: 0.5rem;">Слов для изучения больше нет.</p>';
            document.getElementById('gameArea').style.display = 'none';
            const vl = document.getElementById('vocabListInLearning');
            if (vl) vl.style.display = '';
            return;
          }
          currentQuestion = nextRes.question;
          lastVocabId = currentQuestion.vocab_id;
          document.getElementById('gameFeedback').innerHTML = '';
          const q = currentQuestion;
          document.getElementById('gamePrompt').textContent = q.mode === 'reverse' ? 'Переведите на казахский: ' + q.prompt : 'Переведите на русский: ' + q.prompt;
          const inputArea = document.getElementById('gameInputArea');
          if (q.options && q.options.length) {
            inputArea.innerHTML = '<div class="exercise-options">' + q.options.map((o) =>
              '<label class="exercise-option"><input type="radio" name="gameAnswer" value="' + escapeHtml(o) + '"> ' + escapeHtml(o) + '</label>'
            ).join('') + '</div>';
          } else {
            inputArea.innerHTML = '<input type="text" id="gameAnswerInput" placeholder="Ваш ответ">';
          }
        }, 1500);
      } catch (err) {
        document.getElementById('gameFeedback').innerHTML = '<span class="error">' + escapeHtml(err.data?.detail || err.message) + '</span>';
      }
    });
  }

  // Progress
  async function renderProgress(el) {
    const prog = await api.progress.summary();
    const acc = prog.exercise_attempts ? Math.round((prog.exercise_correct / prog.exercise_attempts) * 100) : 0;
    el.innerHTML = `
      <h1 class="page-title">Прогресс и статистика</h1>
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-value">${prog.completed_lessons} / ${prog.total_lessons}</div>
          <div class="stat-label">Уроков пройдено</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${prog.exercise_attempts}</div>
          <div class="stat-label">Попыток упражнений</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${acc}%</div>
          <div class="stat-label">Правильных ответов</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${prog.test_attempts}</div>
          <div class="stat-label">Тестов пройдено</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${prog.test_passed}</div>
          <div class="stat-label">Тестов сдано</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${prog.vocabulary_size}</div>
          <div class="stat-label">Слов в словаре</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${prog.vocabulary_learned}</div>
          <div class="stat-label">Изучено слов</div>
        </div>
      </div>
    `;
  }

  // Admin
  async function renderAdmin(el) {
    if (user && (user.role === 'teacher' || user.role === 'admin')) {
      el.innerHTML = `
        <h1 class="page-title">Панель преподавателя</h1>
        <div class="card admin-card">
          <h2>Панель преподавателя / администратора</h2>
          <p style="color: #64748b;">Доступно создание уроков, упражнений, тестов и импорт контента через API.</p>
          <a href="/docs" target="_blank" class="btn">Документация API</a>
        </div>
      `;
    } else {
      el.innerHTML = '<div class="card"><div class="error">Доступ запрещён.</div></div>';
    }
  }

  // Handle /lesson/:id
  const path = getPath();
  const lessonMatch = path.match(/^\/lesson\/(\d+)$/);
  if (lessonMatch) {
    loadUser().then(() => {
      setActiveNav();
      const content = document.getElementById('content');
      if (content) showLesson(parseInt(lessonMatch[1]));
    });
  } else {
    init();
  }
})();
