import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Search,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  ExternalLink,
  Copy,
  ChevronDown,
  ChevronUp,
  Blocks,
  Activity,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { runAudit, getAuditTrail, healthCheck } from '../services/api';

// ── Risk-level colour map ────────────────────────────────────────────

const RISK_COLORS = {
  LOW: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', label: '🟢 LOW' },
  MEDIUM: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', label: '🟡 MEDIUM' },
  HIGH: { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400', label: '🟠 HIGH' },
  CRITICAL: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', label: '🔴 CRITICAL' },
};

const SEVERITY_DOTS = {
  LOW: 'bg-emerald-400',
  MEDIUM: 'bg-yellow-400',
  HIGH: 'bg-orange-400',
  CRITICAL: 'bg-red-400',
};

// ── Main Component ───────────────────────────────────────────────────

export default function AuditPage() {
  // Form state
  const [query, setQuery] = useState('');
  const [targetAddress, setTargetAddress] = useState('');
  const [auditType, setAuditType] = useState('general');

  // Execution state
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // UI state
  const [trailExpanded, setTrailExpanded] = useState(false);
  const [trail, setTrail] = useState(null);
  const [weilchainConnected, setWeilchainConnected] = useState(null);
  const [copiedHash, setCopiedHash] = useState(null);

  // Health check on mount
  useEffect(() => {
    healthCheck()
      .then((data) => setWeilchainConnected(data.weilchain_connected))
      .catch(() => setWeilchainConnected(false));
  }, []);

  // ── Run Audit ──────────────────────────────────────────────────────

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (query.length < 10) return;

    setIsLoading(true);
    setError(null);
    setResult(null);
    setTrail(null);

    try {
      const data = await runAudit({
        query,
        target_address: targetAddress || null,
        audit_type: auditType,
      });
      setResult(data);
    } catch (err) {
      setError(err.message || 'Audit failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Fetch Trail ────────────────────────────────────────────────────

  const handleFetchTrail = async () => {
    if (!result?.session_id) return;
    if (trail) {
      setTrailExpanded(!trailExpanded);
      return;
    }

    try {
      const data = await getAuditTrail(result.session_id);
      setTrail(data);
      setTrailExpanded(true);
    } catch {
      setTrail({ entries: [], total_entries: 0 });
      setTrailExpanded(true);
    }
  };

  // ── Copy Hash ──────────────────────────────────────────────────────

  const copyHash = (hash) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  // ── Report helpers ─────────────────────────────────────────────────

  const report = result?.final_report;
  const risk = report ? RISK_COLORS[report.risk_level] || RISK_COLORS.MEDIUM : null;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* ── Header ── */}
      <header className="border-b border-white/5 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-white/60 hover:text-white transition">
            <ArrowLeft size={18} />
            <span className="text-sm">Back</span>
          </Link>
          <div className="flex items-center gap-3">
            <Blocks size={20} className="text-purple-400" />
            <span className="font-bold text-lg">AuditChain</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${weilchainConnected === true ? 'bg-emerald-400' : weilchainConnected === false ? 'bg-red-400' : 'bg-yellow-400 animate-pulse'}`} />
            <span className="text-white/40">
              WeilChain {weilchainConnected === true ? 'Connected' : weilchainConnected === false ? 'Offline' : 'Checking…'}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10">
        {/* ── Audit Form ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <h1 className="text-3xl font-bold mb-2">Run Due Diligence Audit</h1>
          <p className="text-white/50 mb-8">Every step is logged immutably on WeilChain as verifiable proof.</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Query */}
            <div>
              <label className="block text-sm text-white/60 mb-2">Audit Query *</label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Audit wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 for rug-pull risk indicators"
                rows={3}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:border-purple-500/50 transition resize-none"
                required
                minLength={10}
              />
              <span className="text-xs text-white/30 mt-1 block">{query.length}/10 min characters</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Target Address */}
              <div>
                <label className="block text-sm text-white/60 mb-2">Target Address (optional)</label>
                <input
                  type="text"
                  value={targetAddress}
                  onChange={(e) => setTargetAddress(e.target.value)}
                  placeholder="0x..."
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:border-purple-500/50 transition font-mono text-sm"
                />
              </div>

              {/* Audit Type */}
              <div>
                <label className="block text-sm text-white/60 mb-2">Audit Type</label>
                <select
                  value={auditType}
                  onChange={(e) => setAuditType(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500/50 transition appearance-none"
                >
                  <option value="general">🔍 General</option>
                  <option value="wallet">👛 Wallet</option>
                  <option value="contract">📄 Contract</option>
                  <option value="token">🪙 Token</option>
                </select>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading || query.length < 10}
              className="w-full md:w-auto px-8 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl font-semibold flex items-center justify-center gap-2 transition"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Running Audit…
                </>
              ) : (
                <>
                  <Search size={18} />
                  Run Audit
                </>
              )}
            </button>
          </form>
        </motion.div>

        {/* ── Loading State ── */}
        <AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mb-10 p-8 border border-purple-500/20 rounded-2xl bg-purple-500/5 text-center"
            >
              <Loader2 size={40} className="animate-spin text-purple-400 mx-auto mb-4" />
              <p className="text-white/70 text-lg">Agent is investigating…</p>
              <p className="text-white/30 text-sm mt-2">
                Fetching on-chain data → Analysing → Logging to WeilChain
              </p>
              <div className="flex justify-center gap-1 mt-6">
                {[0, 1, 2, 3, 4].map((i) => (
                  <motion.div
                    key={i}
                    className="w-2 h-2 rounded-full bg-purple-400"
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Error State ── */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mb-10 p-6 border border-red-500/20 rounded-2xl bg-red-500/5 flex items-start gap-4"
            >
              <XCircle size={24} className="text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-red-400">Audit Failed</p>
                <p className="text-white/50 text-sm mt-1">{error}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Results ── */}
        <AnimatePresence>
          {result && report && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {/* ── Header Card ── */}
              <div className={`p-6 rounded-2xl border ${risk.border} ${risk.bg}`}>
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div>
                    <p className="text-white/40 text-sm mb-1">Risk Assessment</p>
                    <p className={`text-3xl font-bold ${risk.text}`}>{risk.label}</p>
                  </div>
                  <div className="flex gap-6 text-sm text-white/50">
                    <div>
                      <p className="text-white/30 text-xs">Session</p>
                      <p className="font-mono">{result.session_id.slice(0, 8)}…</p>
                    </div>
                    <div>
                      <p className="text-white/30 text-xs">Steps</p>
                      <p>{result.total_steps}</p>
                    </div>
                    <div>
                      <p className="text-white/30 text-xs">Duration</p>
                      <p>{result.duration_seconds}s</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* ── Summary ── */}
              <div className="p-6 rounded-2xl border border-white/5 bg-white/[0.02]">
                <h3 className="text-sm font-semibold text-white/40 uppercase tracking-wider mb-3">Executive Summary</h3>
                <p className="text-white/80 leading-relaxed">{report.summary}</p>
              </div>

              {/* ── Findings ── */}
              {report.findings?.length > 0 && (
                <div className="p-6 rounded-2xl border border-white/5 bg-white/[0.02]">
                  <h3 className="text-sm font-semibold text-white/40 uppercase tracking-wider mb-4">
                    Findings ({report.findings.length})
                  </h3>
                  <div className="space-y-3">
                    {report.findings.map((f, i) => (
                      <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-white/[0.02] border border-white/5">
                        <div className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${SEVERITY_DOTS[f.severity] || 'bg-gray-400'}`} />
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-semibold text-white/70">{f.category}</span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-white/30">{f.severity}</span>
                          </div>
                          <p className="text-sm text-white/50">{f.detail}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Red Flags ── */}
              {report.red_flags?.length > 0 && (
                <div className="p-6 rounded-2xl border border-red-500/10 bg-red-500/[0.03]">
                  <h3 className="text-sm font-semibold text-red-400/60 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <AlertTriangle size={16} />
                    Red Flags ({report.red_flags.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {report.red_flags.map((flag, i) => (
                      <span key={i} className="px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
                        {flag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Recommendation ── */}
              {report.recommendation && (
                <div className="p-6 rounded-2xl border border-emerald-500/10 bg-emerald-500/[0.03]">
                  <h3 className="text-sm font-semibold text-emerald-400/60 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <CheckCircle size={16} />
                    Recommendation
                  </h3>
                  <p className="text-white/70 leading-relaxed">{report.recommendation}</p>
                </div>
              )}

              {/* ── WeilChain On-Chain Proof ── */}
              <div className="p-6 rounded-2xl border border-purple-500/10 bg-purple-500/[0.03]">
                <h3 className="text-sm font-semibold text-purple-400/60 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Shield size={16} />
                  WeilChain On-Chain Proof
                </h3>
                <p className="text-white/40 text-sm mb-4">
                  Every agent step is immutably recorded. These transaction hashes are your verifiable proof.
                </p>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {result.weilchain_tx_hashes?.map((hash, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5 group">
                      <span className="text-xs text-purple-400 font-mono w-6">#{i}</span>
                      <span className="font-mono text-sm text-white/50 truncate flex-1">{hash}</span>
                      <button
                        onClick={() => copyHash(hash)}
                        className="opacity-0 group-hover:opacity-100 transition text-white/30 hover:text-white"
                        title="Copy hash"
                      >
                        {copiedHash === hash ? <CheckCircle size={14} className="text-emerald-400" /> : <Copy size={14} />}
                      </button>
                      {!hash.startsWith('LOCAL_FALLBACK') && (
                        <a
                          href={`https://explorer.testnet.weilliptic.ai/tx/${hash}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="opacity-0 group-hover:opacity-100 transition text-white/30 hover:text-purple-400"
                          title="View on WeilChain Explorer"
                        >
                          <ExternalLink size={14} />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* ── Audit Trail (expandable) ── */}
              <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
                <button
                  onClick={handleFetchTrail}
                  className="w-full p-6 flex items-center justify-between hover:bg-white/[0.02] transition"
                >
                  <h3 className="text-sm font-semibold text-white/40 uppercase tracking-wider flex items-center gap-2">
                    <Activity size={16} />
                    Full Audit Trail
                  </h3>
                  {trailExpanded ? <ChevronUp size={18} className="text-white/30" /> : <ChevronDown size={18} className="text-white/30" />}
                </button>

                <AnimatePresence>
                  {trailExpanded && trail && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: 'auto' }}
                      exit={{ height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-6 space-y-3">
                        {trail.entries?.length > 0 ? (
                          trail.entries.map((entry, i) => (
                            <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
                              <div className="flex items-center gap-3 mb-2">
                                <span className="text-xs font-mono text-purple-400 bg-purple-400/10 px-2 py-0.5 rounded">
                                  Step {entry.step_index ?? i}
                                </span>
                                <span className="text-xs text-white/30 font-mono">{entry.step_type}</span>
                                {entry.tool_name && (
                                  <span className="text-xs text-white/20">{entry.tool_name}</span>
                                )}
                              </div>
                              {entry.timestamp_utc && (
                                <p className="text-xs text-white/20 font-mono">{entry.timestamp_utc}</p>
                              )}
                            </div>
                          ))
                        ) : (
                          <p className="text-white/30 text-sm">No trail entries found on-chain for this session.</p>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}