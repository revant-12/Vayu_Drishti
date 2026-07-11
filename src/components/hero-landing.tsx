"use client";

import { useState, useEffect } from "react";
import {
  Wind, Brain, Satellite, Shield, MessageCircle, BarChart3,
  ChevronRight, Cpu, Layers, Zap, Globe, ArrowDown,
} from "lucide-react";

interface HeroLandingProps {
  onEnter: () => void;
  stationCount: number;
  cityCount: number;
  avgAqi: number;
}

const FEATURES = [
  {
    icon: Satellite,
    title: "Satellite Intelligence",
    desc: "NASA FIRMS thermal hotspot detection for fire & industrial emission monitoring",
    color: "from-orange-500 to-red-500",
  },
  {
    icon: Brain,
    title: "Multi-Agent AI",
    desc: "5-agent orchestrated system for data fusion, analysis, prediction & advisory",
    color: "from-purple-500 to-indigo-500",
  },
  {
    icon: Cpu,
    title: "ML Forecasting",
    desc: "XGBoost ensemble model with 96.84% accuracy for 72-hour AQI prediction",
    color: "from-cyan-500 to-blue-500",
  },
  {
    icon: Layers,
    title: "Dispersion Modelling",
    desc: "Gaussian plume atmospheric model with Pasquill-Gifford stability classes",
    color: "from-emerald-500 to-teal-500",
  },
  {
    icon: Shield,
    title: "Enforcement Intelligence",
    desc: "Evidence-backed enforcement actions with auto-generated PDF reports",
    color: "from-red-500 to-pink-500",
  },
  {
    icon: MessageCircle,
    title: "Citizen Advisory",
    desc: "Gemini AI-powered multilingual chat in English, Hindi, Tamil, Kannada & Telugu",
    color: "from-amber-500 to-orange-500",
  },
];

const TECH_STACK = [
  "CPCB CAAQMS", "data.gov.in API", "XGBoost", "Gaussian Plume",
  "NASA FIRMS", "Gemini 2.0", "Next.js", "FastAPI", "Leaflet",
];

export default function HeroLanding({ onEnter, stationCount, cityCount, avgAqi }: HeroLandingProps) {
  const [visible, setVisible] = useState(false);
  const [countUp, setCountUp] = useState({ stations: 0, cities: 0, aqi: 0 });

  useEffect(() => {
    setVisible(true);
    const duration = 1500;
    const steps = 40;
    const interval = duration / steps;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      const progress = step / steps;
      const ease = 1 - Math.pow(1 - progress, 3);
      setCountUp({
        stations: Math.round(stationCount * ease),
        cities: Math.round(cityCount * ease),
        aqi: Math.round(avgAqi * ease),
      });
      if (step >= steps) clearInterval(timer);
    }, interval);

    return () => clearInterval(timer);
  }, [stationCount, cityCount, avgAqi]);

  return (
    <div className="min-h-screen bg-zinc-950 text-white overflow-y-auto">
      {/* Animated background grid */}
      <div className="fixed inset-0 opacity-[0.03]" style={{
        backgroundImage: "linear-gradient(rgba(6,182,212,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(6,182,212,0.3) 1px, transparent 1px)",
        backgroundSize: "60px 60px",
      }} />

      {/* Radial glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] opacity-20 pointer-events-none"
        style={{ background: "radial-gradient(ellipse, rgba(6,182,212,0.3) 0%, transparent 70%)" }}
      />

      {/* Hero Section */}
      <section className={`relative z-10 flex flex-col items-center justify-center min-h-screen px-6 transition-all duration-1000 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
        {/* Logo */}
        <div className="mb-6 relative">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shadow-2xl shadow-cyan-500/20">
            <Wind className="w-11 h-11 text-white" />
          </div>
          <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-green-500 border-2 border-zinc-950 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-5xl md:text-7xl font-black tracking-tight text-center mb-3">
          <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">
            VayuBudhi
          </span>
        </h1>
        <p className="text-lg md:text-xl text-zinc-400 text-center max-w-2xl mb-2">
          AI-Powered Urban Air Quality Intelligence Platform
        </p>
        <p className="text-sm text-zinc-600 text-center max-w-xl mb-10">
          From reactive monitoring to proactive, evidence-based intervention —
          giving city administrators the tools to reduce pollution at source.
        </p>

        {/* Live stats */}
        <div className="flex items-center gap-8 md:gap-12 mb-10">
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-black text-cyan-400 tabular-nums">
              {countUp.stations}
            </div>
            <div className="text-[10px] uppercase tracking-widest text-zinc-500 mt-1">Live Stations</div>
          </div>
          <div className="w-px h-12 bg-zinc-800" />
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-black text-emerald-400 tabular-nums">
              {countUp.cities}
            </div>
            <div className="text-[10px] uppercase tracking-widest text-zinc-500 mt-1">Cities Monitored</div>
          </div>
          <div className="w-px h-12 bg-zinc-800" />
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-black text-amber-400 tabular-nums">
              {countUp.aqi}
            </div>
            <div className="text-[10px] uppercase tracking-widest text-zinc-500 mt-1">National Avg AQI</div>
          </div>
        </div>

        {/* CTA Button */}
        <button
          onClick={onEnter}
          className="group relative px-8 py-3.5 rounded-xl font-semibold text-base bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-xl shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all duration-300 hover:scale-105 active:scale-95"
        >
          <span className="flex items-center gap-2">
            Enter Dashboard
            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </span>
        </button>

        {/* Scroll hint */}
        <div className="absolute bottom-8 flex flex-col items-center gap-2 animate-bounce">
          <span className="text-[10px] uppercase tracking-widest text-zinc-600">Explore Features</span>
          <ArrowDown className="w-4 h-4 text-zinc-600" />
        </div>
      </section>

      {/* Features Section */}
      <section className={`relative z-10 px-6 py-20 transition-all duration-1000 delay-300 ${visible ? "opacity-100" : "opacity-0"}`}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium mb-4">
              <Zap className="w-3 h-3" />
              Powered by Multi-Agent AI
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-3">
              Six Intelligence Layers
            </h2>
            <p className="text-zinc-500 max-w-lg mx-auto text-sm">
              Each layer operates as an independent AI agent, orchestrated for
              comprehensive air quality intelligence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f, i) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.title}
                  className="group relative bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-5 hover:border-zinc-700 transition-all duration-300 hover:-translate-y-1"
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${f.color} flex items-center justify-center mb-3 shadow-lg group-hover:scale-110 transition-transform`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-sm font-bold text-white mb-1">{f.title}</h3>
                  <p className="text-xs text-zinc-500 leading-relaxed">{f.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Tech Stack Bar */}
      <section className="relative z-10 px-6 py-12 border-t border-zinc-900">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-6">
            <h3 className="text-xs uppercase tracking-widest text-zinc-600 font-semibold">Technology Stack</h3>
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            {TECH_STACK.map((tech) => (
              <span
                key={tech}
                className="px-3 py-1.5 rounded-md bg-zinc-900 border border-zinc-800 text-[11px] text-zinc-400 font-medium"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Data Sources */}
      <section className="relative z-10 px-6 py-12 border-t border-zinc-900">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium mb-4">
            <Globe className="w-3 h-3" />
            Real-Time Data
          </div>
          <h2 className="text-2xl font-bold mb-3">Not Mock Data. Real India.</h2>
          <p className="text-zinc-500 text-sm max-w-lg mx-auto mb-8">
            Live data from CPCB&apos;s Continuous Ambient Air Quality Monitoring System
            across 8 major Indian cities, updated every 10 minutes.
          </p>

          <div className="grid grid-cols-4 md:grid-cols-8 gap-3">
            {["Delhi", "Mumbai", "Kolkata", "Bengaluru", "Chennai", "Lucknow", "Patna", "Hyderabad"].map((city) => (
              <div key={city} className="bg-zinc-900/50 border border-zinc-800/50 rounded-lg p-2 text-center">
                <div className="text-[10px] font-semibold text-zinc-300">{city}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="relative z-10 px-6 py-16 border-t border-zinc-900">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-3">Ready to explore?</h2>
          <p className="text-zinc-500 text-sm mb-8">
            Access real-time air quality intelligence for India&apos;s major cities.
          </p>
          <button
            onClick={onEnter}
            className="group px-8 py-3.5 rounded-xl font-semibold bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-xl shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all duration-300 hover:scale-105 active:scale-95"
          >
            <span className="flex items-center gap-2">
              Launch Dashboard
              <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </span>
          </button>
          <p className="text-[10px] text-zinc-700 mt-6">
            Built for the ET AI Hackathon 2026 — Problem Statement 5
          </p>
        </div>
      </section>
    </div>
  );
}
