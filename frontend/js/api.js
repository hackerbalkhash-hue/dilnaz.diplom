/**
 * API client for Kazakh Language Learning Assistant
 */
const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('token');
}

function getHeaders(includeAuth = true) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (includeAuth && token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
  });
  const data = res.ok ? await res.json().catch(() => ({})) : null;
  if (!res.ok) {
    const err = new Error(data?.detail || res.statusText);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

const api = {
  auth: {
    login: (email, password) =>
      request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
        headers: getHeaders(false),
      }),
    register: (email, password, full_name) =>
      request('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password, full_name }),
        headers: getHeaders(false),
      }),
  },
  users: {
    me: () => request('/users/me'),
    updateMe: (data) =>
      request('/users/me', { method: 'PATCH', body: JSON.stringify(data) }),
  },
  lessons: {
    list: () => request('/lessons/'),
    get: (id) => request(`/lessons/${id}`),
    getNext: (id) => request(`/lessons/${id}/next`),
    complete: (id) => request(`/lessons/${id}/complete`, { method: 'POST' }),
  },
  exercises: {
    list: (lessonId) =>
      request(lessonId ? `/exercises/?lesson_id=${lessonId}` : '/exercises/'),
    get: (id) => request(`/exercises/${id}`),
    submit: (id, userAnswer) =>
      request(`/exercises/${id}/attempt`, {
        method: 'POST',
        body: JSON.stringify({ user_answer: userAnswer }),
      }),
  },
  tests: {
    list: (lessonId) =>
      request(lessonId ? `/tests/?lesson_id=${lessonId}` : '/tests/'),
    get: (id) => request(`/tests/${id}`),
    getQuestions: (id) => request(`/tests/${id}/questions`),
    startAttempt: (id) =>
      request(`/tests/${id}/attempt`, { method: 'POST' }),
    submitAttempt: (attemptId, answers) =>
      request(`/tests/attempts/${attemptId}/submit`, {
        method: 'POST',
        body: JSON.stringify({ answers }),
      }),
    getAttempt: (attemptId) => request(`/tests/attempts/${attemptId}`),
  },
  assistant: {
    chat: (message, context) =>
      request('/assistant/chat', {
        method: 'POST',
        body: JSON.stringify({
          message,
          context: context || { mode: 'free' },
        }),
      }),
  },
  vocabulary: {
    list: (status) =>
      request(status ? `/vocabulary/?status_filter=${status}` : '/vocabulary/'),
    add: (data) =>
      request('/vocabulary/', { method: 'POST', body: JSON.stringify(data) }),
    updateStatus: (id, status) =>
      request(`/vocabulary/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
    remove: (id) => request(`/vocabulary/${id}`, { method: 'DELETE' }),
    gameNext: (lastVocabId) =>
      request(lastVocabId ? `/vocabulary/game/next?last_vocab_id=${lastVocabId}` : '/vocabulary/game/next'),
    gameAnswer: (vocabId, mode, userAnswer) =>
      request('/vocabulary/game/answer', {
        method: 'POST',
        body: JSON.stringify({ vocab_id: vocabId, mode, user_answer: userAnswer }),
      }),
  },
  progress: {
    summary: () => request('/progress/summary'),
  },
  recommendations: {
    list: () => request('/recommendations/'),
    markRead: (id) =>
      request(`/recommendations/${id}/read`, { method: 'PATCH' }),
  },
};
