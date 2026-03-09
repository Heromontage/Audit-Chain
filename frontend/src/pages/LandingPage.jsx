import React, { useState, useEffect } from 'react';
import {
  ArrowRight,
  Shield,
  Brain,
  Link as LinkIcon,
  FileSearch,
  CheckCircle,
  Blocks,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion, useMotionValue, useSpring } from 'framer-motion';

export default function LandingPage() {
  const [titleHovered, setTitleHovered] = useState(false);

  // ── Custom cursor ──
  const mouseX = useMotionValue(-100);
  const mouseY = useMotionValue(-100);
  const springConfig = { damping: 20, stiffness: 150, mass: 0.5 };
  const smoothX = useSpring(mouseX, springConfig);
  const smoothY = useSpring(mouseY, springConfig);

  useEffect(() => {
    const handleMouseMove = (e) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f] cursor-none">
      {/* ── PURPLE LIQUID GLASS CURSOR ── */}
      <motion.div
        className="fixed pointer-events-none z-50"
        style={{
          x: smoothX,
          y: smoothY,
          translateX: '-50%',
          translateY: '-50%',
        }}
      >
        <div
          className="absolute rounded-full"
          style={{
            width: '250px',
            height: '250px',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background:
              'radial-gradient(circle, rgba(108,43,217,0.15) 0%, transparent 70%)',
            filter: 'blur(30px)',
          }}
        />
        <div
          className="relative rounded-full"
          style={{
            width: '120px',
            height: '120px',
            background:
              'radial-gradient(circle at 40% 40%, rgba(108,43,217,0.35) 0%, rgba(108,43,217,0.15) 40%, rgba(108,43,217,0.05) 70%, transparent 100%)',
            filter: 'blur(20px)',
            boxShadow: '0 0 40px rgba(108,43,217,0.2)',
          }}
        />
        <div
          className="absolute rounded-full"
          style={{
            width: '8px',
            height: '8px',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: '#6c2bd9',
            boxShadow: '0 0 10px #6c2bd9, 0 0 20px rgba(108,43,217,0.5)',
          }}
        />
      </motion.div>

      {/* ════════════════════════════════════
          HERO SECTION
         ════════════════════════════════════ */}
      <section className="relative min-h-screen flex items-center overflow-hidden px-6 py-24">
        {/* Background blobs */}
        <div
          className="absolute top-0 left-0 w-[600px] h-[600px] rounded-full blur-[150px] pointer-events-none opacity-20"
          style={{
            background:
              'radial-gradient(circle, rgba(108,43,217,0.5) 0%, transparent 70%)',
          }}
        />
        <div
          className="absolute bottom-0 right-0 w-[500px] h-[500px] rounded-full blur-[150px] pointer-events-none opacity-20"
          style={{
            background:
              'radial-gradient(circle, rgba(79,70,229,0.5) 0%, transparent 70%)',
          }}
        />

        <div className="relative z-10 w-full max-w-7xl mx-auto">
          {/* Badge */}
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs mb-12"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#9ca3af',
            }}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span
              className="w-2 h-2 rounded-full animate-pulse"
              style={{
                background: '#4ade80',
                boxShadow: '0 0 10px #4ade80',
              }}
            />
            Weilliptic Hackathon 2026 · PS2
          </motion.div>

          {/* ── TITLE — plain text, hover = transparent ── */}
          <motion.div
            className="mb-10"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
            onMouseEnter={() => setTitleHovered(true)}
            onMouseLeave={() => setTitleHovered(false)}
          >
            <h1
              className="text-7xl md:text-8xl lg:text-9xl font-bold leading-[0.9] tracking-tight cursor-none transition-all duration-300"
              style={{
                color: '#ffffff',
                opacity: titleHovered ? 0.6 : 1,
                textShadow: titleHovered
                  ? '0 0 30px rgba(108,43,217,0.5), 0 0 60px rgba(108,43,217,0.25)'
                  : 'none',
              }}
            >
              AUDIT
              <br />
              CHAIN
            </h1>
          </motion.div>

          {/* Subtitle */}
          <motion.p
            className="text-xl md:text-2xl max-w-2xl leading-relaxed cursor-none text-gray-500 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            On-chain audited{' '}
            <span className="text-purple-300 font-semibold">AI agent</span> for
            automated due diligence in{' '}
            <span className="text-indigo-300 font-semibold">Web3</span>.
            Verifiable. Immutable. Trustless.
          </motion.p>

          {/* CTA Button */}
          <motion.div
            className="flex gap-4 mb-20"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
          >
            <a
              href="#features"
              className="group inline-flex items-center justify-center gap-3 px-10 py-5 rounded-2xl text-xl font-semibold text-white transition-all hover:scale-105 cursor-none"
              style={{
                background: 'linear-gradient(135deg, #6c2bd9, #4f46e5)',
                boxShadow: '0 10px 40px rgba(108,43,217,0.3)',
              }}
            >
              Get Started
              <ArrowRight
                className="group-hover:translate-x-1 transition-transform"
                size={24}
              />
            </a>
          </motion.div>

          {/* Stats */}
          <motion.div
            className="flex flex-wrap gap-12"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8, duration: 0.6 }}
          >
            {[
              { label: 'PLATFORM', value: 'Weilchain', color: '#C084FC' },
              { label: 'FRAMEWORK', value: 'LangGraph', color: '#818CF8' },
              { label: 'LANGUAGE', value: 'Python', color: '#C084FC' },
              { label: 'CATEGORY', value: 'AI + Chain', color: '#818CF8' },
            ].map((stat, i) => (
              <div key={i} className="cursor-none">
                <div
                  className="text-3xl font-bold font-mono"
                  style={{ color: stat.color }}
                >
                  {stat.value}
                </div>
                <div className="text-xs text-gray-600 mt-1 uppercase tracking-wider">
                  {stat.label}
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ════════════════════════════════════
          HOW IT WORKS
         ════════════════════════════════════ */}
      <section className="relative py-32 px-6" id="how-it-works">
        <div className="max-w-5xl mx-auto">
          <motion.h2
            className="text-5xl md:text-7xl font-bold text-center mb-20 cursor-none text-white"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            How It Works
          </motion.h2>

          <div className="space-y-8">
            {[
              {
                num: '01',
                title: 'User Input',
                desc: 'Submit a query — "Analyse wallet 0x…" or "Audit this contract" — via CLI or frontend.',
              },
              {
                num: '02',
                title: 'LangGraph Agent Loop',
                desc: 'Agent decomposes the task into sub-steps — fetching data, calling tools, LLM reasoning, deciding next actions.',
              },
              {
                num: '03',
                title: 'Tool Execution via MCP',
                desc: 'Agent invokes blockchain explorers, token APIs through the Weilchain MCP applet framework.',
              },
              {
                num: '04',
                title: 'Audit Logging to Weilchain',
                desc: 'After every step, a structured log is pushed to Weilchain via Python SDK — creating an immutable on-chain audit trail.',
              },
              {
                num: '05',
                title: 'Final Report + Proof',
                desc: 'User receives a due diligence report alongside a Weilchain transaction hash as verifiable proof.',
              },
            ].map((step, i) => (
              <motion.div
                key={i}
                className="flex items-start gap-6 p-6 rounded-2xl cursor-none transition-all duration-300 hover:bg-white/[0.03]"
                style={{
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
              >
                <div
                  className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center text-white font-mono font-bold text-sm"
                  style={{
                    background: 'linear-gradient(135deg, #6c2bd9, #4f46e5)',
                  }}
                >
                  {step.num}
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    {step.title}
                  </h3>
                  <p className="text-gray-400 leading-relaxed">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════
          FEATURES
         ════════════════════════════════════ */}
      <section className="relative py-32 px-6" id="features">
        <div className="max-w-6xl mx-auto">
          <motion.h2
            className="text-5xl md:text-7xl font-bold text-center mb-20 cursor-none text-white"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            Why AuditChain?
          </motion.h2>

          <div className="grid md:grid-cols-2 gap-8">
            {[
              {
                icon: <Shield size={32} />,
                title: 'Immutable Audit Trail',
                desc: 'Every AI reasoning step, tool call, and decision is logged on-chain. No tampering, ever.',
                color: '#6c2bd9',
              },
              {
                icon: <CheckCircle size={32} />,
                title: 'On-Chain Trust Verification',
                desc: 'Anyone can inspect and verify the AI\'s full decision trail via Weilchain transaction hashes.',
                color: '#4f46e5',
              },
              {
                icon: <Brain size={32} />,
                title: 'Composable Agentic Workflow',
                desc: 'LangGraph multi-step agent loop with tool execution, error handling, and control logic.',
                color: '#6c2bd9',
              },
              {
                icon: <FileSearch size={32} />,
                title: 'Automated Due Diligence',
                desc: 'Analyse wallets, audit contracts, and generate investment signals — all verifiable.',
                color: '#4f46e5',
              },
              {
                icon: <Blocks size={32} />,
                title: 'MCP Tool Integration',
                desc: 'Blockchain explorers and token APIs integrated through Weilchain MCP applet framework.',
                color: '#6c2bd9',
              },
              {
                icon: <LinkIcon size={32} />,
                title: 'Dispute-Proof AI Outputs',
                desc: 'Prove what the AI reasoned, which tools it called, when, and why. End-to-end accountability.',
                color: '#4f46e5',
              },
            ].map((f, i) => (
              <motion.div
                key={i}
                className="p-8 rounded-3xl cursor-none transition-all duration-400 hover:-translate-y-2"
                style={{
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
              >
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6 text-white"
                  style={{
                    background: `linear-gradient(135deg, ${f.color}, ${f.color}dd)`,
                  }}
                >
                  {f.icon}
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  {f.title}
                </h3>
                <p className="text-gray-400 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════
          TECH STACK
         ════════════════════════════════════ */}
      <section className="relative py-32 px-6" id="tech">
        <div className="max-w-4xl mx-auto">
          <motion.h2
            className="text-5xl md:text-7xl font-bold text-center mb-20 cursor-none text-white"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            Tech Stack
          </motion.h2>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { emoji: '🔗', label: 'LangChain / LangGraph' },
              { emoji: '⛓️', label: 'Weilchain Python SDK' },
              { emoji: '🔧', label: 'Weilchain MCP Applets' },
              { emoji: '🤖', label: 'OpenAI / Gemini LLM' },
              { emoji: '📊', label: 'Etherscan / Alchemy' },
              { emoji: '🐍', label: 'Python FastAPI' },
            ].map((tech, i) => (
              <motion.div
                key={i}
                className="p-5 rounded-xl cursor-none text-center transition-all duration-300 hover:bg-white/[0.04]"
                style={{
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
              >
                <div className="text-3xl mb-3">{tech.emoji}</div>
                <div className="text-sm text-gray-300 font-medium">
                  {tech.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════
          TIMELINE
         ════════════════════════════════════ */}
      <section className="relative py-32 px-6" id="timeline">
        <div className="max-w-4xl mx-auto">
          <motion.h2
            className="text-5xl md:text-7xl font-bold text-center mb-20 cursor-none text-white"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            Timeline
          </motion.h2>

          <div className="space-y-6">
            {[
              {
                date: '25 Feb 2026',
                label: 'Idea Submission',
                desc: 'Document + slides submitted',
                done: true,
              },
              {
                date: '14 Mar 2026',
                label: 'Midterm Demo',
                desc: 'Working agent with audit logging',
                done: false,
              },
              {
                date: '16 Mar 2026',
                label: 'Final Submission',
                desc: 'Full system + on-chain proof + demo video',
                done: false,
              },
            ].map((item, i) => (
              <motion.div
                key={i}
                className="flex items-center gap-6 p-5 rounded-xl cursor-none"
                style={{
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
                initial={{ opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.6 }}
              >
                <div
                  className="flex-shrink-0 w-3 h-3 rounded-full"
                  style={{
                    background: item.done ? '#4ade80' : '#6c2bd9',
                    boxShadow: item.done
                      ? '0 0 10px #4ade80'
                      : '0 0 10px rgba(108,43,217,0.5)',
                  }}
                />
                <div className="min-w-[120px] font-mono text-sm font-semibold text-purple-300">
                  {item.date}
                </div>
                <div>
                  <span className="text-white font-semibold">{item.label}</span>
                  <span className="text-gray-500 ml-2">— {item.desc}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════
          FOOTER
         ════════════════════════════════════ */}
      <footer
        className="py-10 px-6"
        style={{
          borderTop: '1px solid rgba(255,255,255,0.05)',
          background: '#07070b',
        }}
      >
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-gray-600 text-sm">
            Weilliptic Hackathon 2026 · IIT Mandi
          </p>
          <div className="text-sm font-semibold text-purple-400">
            AuditChain · PS2 Submission
          </div>
        </div>
      </footer>
    </div>
  );
}