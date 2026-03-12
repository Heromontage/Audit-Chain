/**
 * AuditChain — Backend API Client
 *
 * Wraps all 4 FastAPI endpoints with clean async functions.
 * Uses native fetch (no Axios dependency needed).
 */

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

/**
 * Generic fetch wrapper with error handling.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(
      errorData.detail || `API Error: ${response.status} ${response.statusText}`
    );
    error.status = response.status;
    error.data = errorData;
    throw error;
  }

  return response.json();
}

// ── POST /audit — Launch a new audit session ──────────────────────────

/**
 * Start a new Web3 due-diligence audit.
 *
 * @param {object} params
 * @param {string} params.query       - Audit query (min 10 chars)
 * @param {string} [params.target_address] - Optional 0x address
 * @param {string} [params.audit_type]     - "wallet"|"contract"|"token"|"general"
 * @returns {Promise<object>} AuditResponse
 */
export async function runAudit({ query, target_address = null, audit_type = 'general' }) {
  return request('/audit', {
    method: 'POST',
    body: JSON.stringify({ query, target_address, audit_type }),
  });
}

// ── GET /audit/:sessionId/trail — Fetch audit trail ──────────────────

/**
 * Fetch the full on-chain audit trail for a session.
 *
 * @param {string} sessionId
 * @returns {Promise<object>} AuditTrailResponse
 */
export async function getAuditTrail(sessionId) {
  return request(`/audit/${sessionId}/trail`);
}

// ── GET /audit/:sessionId/report — Fetch final report ────────────────

/**
 * Fetch only the final due-diligence report for a session.
 *
 * @param {string} sessionId
 * @returns {Promise<object>} Report payload
 */
export async function getAuditReport(sessionId) {
  return request(`/audit/${sessionId}/report`);
}

// ── GET /health — Health check ───────────────────────────────────────

/**
 * Check API and WeilChain connectivity.
 *
 * @returns {Promise<object>} HealthResponse
 */
export async function healthCheck() {
  return request('/health');
}

export default {
  runAudit,
  getAuditTrail,
  getAuditReport,
  healthCheck,
};