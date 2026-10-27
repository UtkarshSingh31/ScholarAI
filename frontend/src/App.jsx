import React, { useState, useEffect, useRef } from 'react';

// --- Minimalist / Technical Icons ---
const IconCheck = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square"><polyline points="20 6 9 17 4 12"></polyline></svg>;
const IconX = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>;
const IconAlert = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>;
const IconArrowRight = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>;
const IconExternal = () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>;
const IconTerminal = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>;
const IconActivity = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>;
const IconDatabase = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>;
const IconFile = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>;

const NODES = [
  { id: 'profile_intelligence', label: 'SYS.PROFILE_INIT' },
  { id: 'supervisor_profile', label: 'ROUT.VALIDATE' },
  { id: 'opportunity_hunter', label: 'AGT.HUNTER' },
  { id: 'evidence', label: 'AGT.EVIDENCE' },
  { id: 'eligibility_auditor', label: 'AGT.AUDITOR' },
  { id: 'matchmaker', label: 'SYS.MATCHMAKER' }
];

// --- UI Primitives ---

const Input = ({ label, type = "text", required, placeholder, value, onChange }) => (
  <div className="flex flex-col group">
    <label className="font-mono text-[10px] uppercase tracking-widest text-neutral-500 mb-1 flex justify-between">
      {label} {required && <span className="text-blue-500">REQ</span>}
    </label>
    <input
      type={type}
      className="bg-transparent border-b border-neutral-800 py-2 text-sm text-neutral-200 focus:outline-none focus:border-neutral-400 focus:bg-neutral-900/50 transition-colors placeholder:text-neutral-700 rounded-none"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required={required}
    />
  </div>
);

const Select = ({ label, required, options, value, onChange }) => (
  <div className="flex flex-col group">
    <label className="font-mono text-[10px] uppercase tracking-widest text-neutral-500 mb-1 flex justify-between">
      {label} {required && <span className="text-blue-500">REQ</span>}
    </label>
    <select
      className="bg-transparent border-b border-neutral-800 py-2 text-sm text-neutral-200 focus:outline-none focus:border-neutral-400 focus:bg-neutral-900/50 transition-colors appearance-none rounded-none"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required={required}
    >
      <option value="" disabled className="bg-neutral-950">SELECT_</option>
      {options.map(opt => <option key={opt.value} value={opt.value} className="bg-neutral-950">{opt.label}</option>)}
    </select>
  </div>
);

const FileInput = ({ label, required, onChange }) => (
  <div className="flex flex-col group">
    <label className="font-mono text-[10px] uppercase tracking-widest text-neutral-500 mb-1 flex justify-between">
      {label} {required && <span className="text-blue-500">REQ</span>}
    </label>
    <input
      type="file"
      className="bg-transparent border-b border-neutral-800 py-1.5 text-sm text-neutral-400 focus:outline-none focus:border-neutral-400 transition-colors file:mr-4 file:py-1 file:px-3 file:border-0 file:text-[10px] file:font-mono file:uppercase file:tracking-wider file:bg-neutral-900 file:text-neutral-300 hover:file:bg-neutral-800 file:cursor-pointer file:transition-colors"
      onChange={(e) => onChange(e.target.files[0])}
      required={required}
    />
  </div>
);

const SectionHeading = ({ title, num }) => (
  <div className="flex items-center gap-3 mb-6 mt-12 first:mt-0 border-b border-neutral-800 pb-2">
    <span className="font-mono text-xs text-neutral-500">{num}</span>
    <h3 className="text-sm font-medium tracking-wide text-neutral-200 uppercase">{title}</h3>
  </div>
);

const safeSourceUrl = (value) => {
  try {
    const url = new URL(String(value || ''), window.location.origin);
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.href : '';
  } catch {
    return '';
  }
};

export default function App() {
  const [appState, setAppState] = useState('intake'); // intake, running, completed
  const [formProfile, setFormProfile] = useState({});
  const [missingFields, setMissingFields] = useState([]);
  
  // Dashboard State
  const [currentNodeId, setCurrentNodeId] = useState('');
  const [events, setEvents] = useState([]);
  const [stats, setStats] = useState({ hits: 0, scraped: 0, audited: 0, matches: 0 });
  const [results, setResults] = useState([]);
  const [selectedRecId, setSelectedRecId] = useState(null);
  const [files, setFiles] = useState([]);
  const [error, setError] = useState('');
  
  const terminalEndRef = useRef(null);

  useEffect(() => {
    if (terminalEndRef.current) terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const handleStart = async () => {
    const required = [
      'fullName', 'nationality', 'currentDegreeLevel', 'currentDegreeName', 
      'currentField', 'graduationStatus', 'targetDegree', 'targetField', 
      'targetIntake', 'preferredCountries', 'fundingRequirement'
    ];
    const missing = required.filter(f => !formProfile[f]);
    if (missing.length > 0) {
      setMissingFields(missing);
      return;
    }
    setMissingFields([]);
    setError('');
    setAppState('running');
    const countries = String(formProfile.preferredCountries || '')
      .split(',')
      .map(value => value.trim())
      .filter(Boolean);
    const degreeLevels = { hs: 'secondary_school', bsc: 'bachelors', msc: 'masters', phd: 'phd' };
    const targetLevels = { bsc: 'bachelors', msc: 'masters', phd: 'phd' };
    const profile = {
      name: formProfile.fullName,
      nationality: formProfile.nationality,
      current_degree_level: degreeLevels[formProfile.currentDegreeLevel] || formProfile.currentDegreeLevel,
      degree: formProfile.currentDegreeName,
      field_of_study: formProfile.currentField,
      graduation_status: formProfile.graduationStatus,
      graduation_date: formProfile.gradDate || null,
      cgpa: formProfile.cgpa ? Number(formProfile.cgpa) : null,
      cgpa_scale: formProfile.scale || null,
      target_degree_level: targetLevels[formProfile.targetDegree] || formProfile.targetDegree,
      target_field: formProfile.targetField,
      target_intake: formProfile.targetIntake,
      preferred_countries: countries,
      budget: formProfile.fundingRequirement,
      funding_need: formProfile.fundingRequirement,
    };
    const data = new FormData();
    data.append('profile', JSON.stringify(profile));
    data.append('profile_urls', JSON.stringify(
      formProfile.portfolioLink ? [formProfile.portfolioLink] : [],
    ));
    files.forEach(file => data.append('documents', file));
    try {
      const response = await fetch('/workflow/jobs', { method: 'POST', body: data });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail?.message || payload.detail || 'Workflow submission failed.');
      }
      await pollJob(payload.status_url);
    } catch (requestError) {
      setError(requestError.message);
      setAppState('intake');
    }
  };

  const pollJob = async (url) => {
    const response = await fetch(url);
    const job = await response.json();
    if (!response.ok) throw new Error(job.detail || 'Workflow status request failed.');
    const jobEvents = job.events || [];
    setEvents(jobEvents.flatMap(event => (event.details || []).map((msg, index) => ({
      id: `${event.timestamp}-${index}`,
      time: event.timestamp?.split('T')[1]?.split('.')[0] || '',
      node: event.label || event.node,
      msg,
      type: event.node?.startsWith('supervisor_') ? 'sys' : 'log',
    }))));
    setCurrentNodeId(job.current_node || '');
    const counts = jobEvents[jobEvents.length - 1]?.counts || {};
    setStats({
      hits: counts.opportunities || 0,
      scraped: counts.evidence || 0,
      audited: counts.eligibility || 0,
      matches: counts.shortlist || 0,
    });
    if (job.status === 'completed' || job.status === 'failed') {
      if (job.status === 'failed') throw new Error((job.errors || []).join(' ') || 'Workflow failed.');
      const result = job.result || {};
      const sourceResults = result.shortlist?.length
        ? result.shortlist
        : (result.eligibility_results || []).slice(0, 10);
      const mappedResults = sourceResults.map((item, index) => ({
        id: item.source_url || `match-${index}`,
        name: item.opportunity_name || 'Opportunity',
        country: item.country || 'Unknown',
        degreeLevel: profileLabel(item.target_degree_level || item.degree_level),
        field: item.target_field || item.field_of_study || 'Not specified',
        funding: item.funding_summary || 'Not specified',
        deadline: item.deadline || 'Unknown',
        status: item.status === 'does_not_meet' ? 'fails' : item.status || 'unknown',
        sourceType: item.source_type || 'source',
        link: item.source_url,
        score: item.ranking_score,
        eligibilityMatrix: (item.requirements || []).map(requirement => ({
          req: requirement.category,
          asks: requirement.value || requirement.requirement,
          has: requirement.profile_value || 'Not provided',
          decision: requirement.decision === 'does_not_meet' ? 'fails' : requirement.decision,
          quote: requirement.evidence_quote || 'No source quote available.',
        })),
      }));
      setResults(mappedResults);
      setSelectedRecId(mappedResults[0]?.id || null);
      setAppState('completed');
      return;
    }
    window.setTimeout(() => pollJob(url).catch(requestError => {
      setError(requestError.message);
      setAppState('intake');
    }), 1000);
  };

  const profileLabel = value => String(value || '').replaceAll('_', ' ');

  // --- Views ---

  const renderIntake = () => (
    <div className="flex min-h-screen bg-[#050505] text-neutral-300 selection:bg-neutral-800">
      
      {/* Left Static Panel */}
      <div className="hidden lg:flex flex-col w-[400px] border-r border-neutral-900 bg-[#0a0a0a] p-10 justify-between fixed h-screen">
        <div>
          <div className="flex items-center gap-2 mb-16">
            <div className="w-4 h-4 bg-white"></div>
            <span className="font-mono text-sm tracking-widest text-white uppercase">Scholar.AI</span>
          </div>
          
          <h1 className="text-3xl text-white font-light tracking-tight mb-4">Define Parameters.</h1>
          <p className="text-sm text-neutral-500 leading-relaxed mb-8">
            The autonomous pipeline requires a strict baseline to prevent hallucination during the audit phase. Complete all required fields to initialize the extraction agent.
          </p>

          <div className="space-y-4 font-mono text-[10px] text-neutral-600 uppercase">
            <div className="flex justify-between border-b border-neutral-900 pb-2">
              <span>Agent Protocol</span> <span>v2.4.1</span>
            </div>
            <div className="flex justify-between border-b border-neutral-900 pb-2">
              <span>Strict Mode</span> <span className="text-emerald-500">Enabled</span>
            </div>
            <div className="flex justify-between border-b border-neutral-900 pb-2">
              <span>Extraction Agent</span> <span className="text-neutral-500">Standby</span>
            </div>
          </div>
        </div>

        <div className="text-[10px] font-mono text-neutral-700 uppercase">
          Sys.Ready // Awaiting Input
        </div>
      </div>

      {/* Right Scrollable Form */}
      <div className="flex-1 lg:ml-[400px] p-8 md:p-16 lg:p-24 max-w-4xl">
        
        {missingFields.length > 0 && (
          <div className="mb-12 border border-red-900/50 bg-red-950/20 p-4 font-mono text-xs text-red-400">
            <div className="flex items-center gap-2 mb-2 font-bold"><IconAlert /> MISSING_REQUIRED_PARAMS</div>
            <span className="text-red-500/70">ERR: Execution halted. Provide values for: {missingFields.join(', ')}</span>
          </div>
        )}

        <div className="space-y-16">
          <div>
            <SectionHeading num="01" title="Current Education Profile" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
              <Input label="Full Name" required placeholder="Jane Doe" value={formProfile.fullName||''} onChange={v=>setFormProfile({...formProfile, fullName:v})} />
              <Input label="Nationality" required placeholder="ISO Country Code or Name" value={formProfile.nationality||''} onChange={v=>setFormProfile({...formProfile, nationality:v})} />
              
              <Select label="Current Degree Level" required options={[{label:"High School", value:"hs"}, {label:"Bachelor's", value:"bsc"}, {label:"Master's", value:"msc"}]} value={formProfile.currentDegreeLevel||''} onChange={v=>setFormProfile({...formProfile, currentDegreeLevel:v})} />
              <Input label="Current Degree Name" required placeholder="BSc Computer Science" value={formProfile.currentDegreeName||''} onChange={v=>setFormProfile({...formProfile, currentDegreeName:v})} />
              
              <Input label="Current Field" required placeholder="e.g., Software Engineering" value={formProfile.currentField||''} onChange={v=>setFormProfile({...formProfile, currentField:v})} />
              <Select label="Graduation Status" required options={[{label:"Enrolled", value:"enrolled"}, {label:"Graduated", value:"graduated"}]} value={formProfile.graduationStatus||''} onChange={v=>setFormProfile({...formProfile, graduationStatus:v})} />
              
              <Input label="Graduation Date / Expected" type="month" value={formProfile.gradDate||''} onChange={v=>setFormProfile({...formProfile, gradDate:v})} />
              <div className="grid grid-cols-2 gap-4">
                <Input label="CGPA / %" placeholder="3.8" value={formProfile.cgpa||''} onChange={v=>setFormProfile({...formProfile, cgpa:v})} />
                <Input label="Scale" placeholder="4.0 or 100" value={formProfile.scale||''} onChange={v=>setFormProfile({...formProfile, scale:v})} />
              </div>
            </div>
          </div>

          <div>
            <SectionHeading num="02" title="Target Study Goal" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
              <Select label="Target Degree Level" required options={[{label:"Bachelor's", value:"bsc"}, {label:"Master's", value:"msc"}, {label:"PhD", value:"phd"}]} value={formProfile.targetDegree||''} onChange={v=>setFormProfile({...formProfile, targetDegree:v})} />
              <Input label="Target Field" required placeholder="Artificial Intelligence" value={formProfile.targetField||''} onChange={v=>setFormProfile({...formProfile, targetField:v})} />
              
              <Input label="Target Intake / Year" required placeholder="Fall 2026" value={formProfile.targetIntake||''} onChange={v=>setFormProfile({...formProfile, targetIntake:v})} />
              <Input label="Preferred Countries" required placeholder="USA, UK, Canada" value={formProfile.preferredCountries||''} onChange={v=>setFormProfile({...formProfile, preferredCountries:v})} />
              
              <Select label="Funding Requirement" required options={[{label:"Full Ride", value:"full"}, {label:"Partial/Tuition", value:"partial"}, {label:"Any", value:"any"}]} value={formProfile.fundingRequirement||''} onChange={v=>setFormProfile({...formProfile, fundingRequirement:v})} />
            </div>
          </div>

          <div>
            <SectionHeading num="03" title="Assets & Verification" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
              <FileInput label="Resume / CV Upload" onChange={f=>setFiles(current => [...current.filter(file => file.name !== f.name), f])} />
              <FileInput label="Transcript / Marksheet" onChange={f=>setFiles(current => [...current.filter(file => file.name !== f.name), f])} />
              <div className="col-span-1 md:col-span-2">
                <Input label="GitHub / LinkedIn / Portfolio Link" placeholder="https://..." value={formProfile.portfolioLink||''} onChange={v=>setFormProfile({...formProfile, portfolioLink:v})} />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-16 flex justify-end border-t border-neutral-900 pt-8">
          <button 
            onClick={handleStart}
            className="bg-white text-black px-8 py-3 text-sm font-medium tracking-wide hover:bg-neutral-200 transition-colors flex items-center gap-3"
          >
            INITIALIZE EXTRACTION AGENT <IconArrowRight />
          </button>
        </div>
        {error && <div className="mt-6 border border-red-900/50 bg-red-950/20 p-4 font-mono text-xs text-red-400">{error}</div>}
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div className="h-screen flex flex-col bg-[#050505] text-neutral-300 font-sans overflow-hidden">
      
      {/* Header */}
      <header className="h-14 border-b border-neutral-900 flex items-center justify-between px-6 shrink-0 bg-[#0a0a0a]">
        <div className="flex items-center gap-4">
          <div className="w-3 h-3 bg-white"></div>
          <span className="font-mono text-xs text-white uppercase tracking-widest">Scholar.AI Console</span>
        </div>
        <div className="flex items-center gap-6 font-mono text-[10px] uppercase tracking-wider">
          <div className="flex items-center gap-2">
            <span className="text-neutral-500">Status</span>
            {appState === 'running' ? (
              <span className="text-blue-400 flex items-center gap-1"><span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"></span> PROCESSING</span>
            ) : (
              <span className="text-emerald-400 flex items-center gap-1"><IconCheck /> TERMINATED_OK</span>
            )}
          </div>
          <div className="w-px h-4 bg-neutral-800"></div>
          <span className="text-neutral-500">REQ-ID: <span className="text-neutral-300">TRX-8829</span></span>
        </div>
      </header>

      {/* Main Area */}
      {appState === 'running' ? (
        <div className="flex-1 p-6 flex flex-col gap-6 overflow-hidden">
          {/* Metrics Bento Row */}
          <div className="grid grid-cols-4 gap-4 shrink-0">
            {[
              { label: 'RAW_HITS', val: stats.hits, icon: IconDatabase },
              { label: 'SCRAPED_URLS', val: stats.scraped, icon: IconFile },
              { label: 'AUDITED_PROFS', val: stats.audited, icon: IconActivity },
              { label: 'VALID_MATCHES', val: stats.matches, icon: IconCheck, highlight: true }
            ].map(m => (
              <div key={m.label} className={`border p-4 flex flex-col justify-between h-24 ${m.highlight ? 'border-white/20 bg-white/5 text-white' : 'border-neutral-900 bg-[#0a0a0a]'}`}>
                <div className="flex justify-between items-start text-neutral-500">
                  <span className="font-mono text-[10px] uppercase">{m.label}</span>
                  <m.icon />
                </div>
                <span className="font-mono text-2xl">{m.val}</span>
              </div>
            ))}
          </div>

          {/* Diagram & Terminal Split */}
          <div className="flex-1 flex gap-6 min-h-0">
            
            {/* Left: Node Diagram */}
            <div className="w-1/3 border border-neutral-900 bg-[#0a0a0a] flex flex-col relative overflow-hidden">
              <div className="p-3 border-b border-neutral-900 font-mono text-[10px] uppercase text-neutral-500 tracking-widest flex justify-between">
                Topology Map <span>Live</span>
              </div>
              <div className="flex-1 p-8 flex flex-col gap-8 relative">
                {/* Connecting Line */}
                <div className="absolute top-10 bottom-10 left-[2.35rem] w-px bg-neutral-800 z-0"></div>
                
                {NODES.map((node) => {
                  const isActive = currentNodeId === node.id;
                  const isPast = NODES.findIndex(n => n.id === currentNodeId) > NODES.findIndex(n => n.id === node.id);
                  return (
                    <div key={node.id} className={`relative z-10 flex items-center gap-4 ${isActive ? 'opacity-100' : isPast ? 'opacity-50' : 'opacity-20'}`}>
                      <div className={`w-3 h-3 border ${isActive ? 'bg-blue-500 border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]' : isPast ? 'bg-neutral-700 border-neutral-500' : 'bg-[#0a0a0a] border-neutral-700'}`}></div>
                      <span className="font-mono text-xs uppercase tracking-wide">{node.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right: Terminal Log */}
            <div className="w-2/3 border border-neutral-900 bg-black flex flex-col">
               <div className="p-3 border-b border-neutral-900 font-mono text-[10px] uppercase text-neutral-500 flex gap-4">
                <span className="text-white flex items-center gap-2"><IconTerminal /> STDOUT</span>
                <span>/var/log/agent.log</span>
              </div>
              <div className="flex-1 overflow-y-auto p-4 font-mono text-xs tracking-tight leading-relaxed custom-scrollbar">
                {events.map(e => (
                  <div key={e.id} className="mb-1 flex gap-4 hover:bg-white/5 px-2 py-0.5 rounded-sm transition-colors">
                    <span className="text-neutral-600 shrink-0">{e.time}</span>
                    <span className={`w-24 shrink-0 ${e.type === 'warn' ? 'text-yellow-500' : e.type === 'ok' ? 'text-emerald-500' : 'text-blue-500'}`}>
                      [{e.node}]
                    </span>
                    <span className={e.type === 'action' ? 'text-white' : 'text-neutral-400'}>{e.msg}</span>
                  </div>
                ))}
                <div ref={terminalEndRef} className="h-2"></div>
              </div>
            </div>

          </div>
        </div>
      ) : (
        /* Results Master-Detail View */
        <div className="flex-1 flex min-h-0">
          
          {/* Left: Master List */}
          <div className="w-[350px] border-r border-neutral-900 flex flex-col bg-[#0a0a0a] shrink-0">
            <div className="p-4 border-b border-neutral-900 flex justify-between items-center">
              <span className="font-mono text-[10px] uppercase text-neutral-500">Discovered Set</span>
              <span className="font-mono text-xs bg-white text-black px-2 py-0.5">{results.length} Nodes</span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
              {results.map(rec => (
                <div 
                  key={rec.id} 
                  onClick={() => setSelectedRecId(rec.id)}
                  className={`p-4 border text-left cursor-pointer transition-colors ${
                    selectedRecId === rec.id 
                      ? 'bg-neutral-900 border-neutral-700' 
                      : 'bg-transparent border-transparent hover:border-neutral-800'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-mono text-[10px] text-neutral-500">{rec.id}</span>
                    <span className={`w-2 h-2 rounded-full ${rec.status === 'meets' ? 'bg-emerald-500' : rec.status === 'fails' ? 'bg-red-500' : 'bg-yellow-500'}`}></span>
                  </div>
                  <h4 className="text-sm font-medium text-white mb-1 truncate">{rec.name}</h4>
                  <div className="flex gap-3 text-xs text-neutral-500">
                    <span>{rec.country}</span>
                    <span>•</span>
                    <span>{rec.degreeLevel}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Detail Matrix View */}
          <div className="flex-1 flex flex-col overflow-y-auto bg-[#050505]">
            {selectedRecId && (
              <div className="max-w-5xl w-full mx-auto p-8 md:p-12">
                
                {/* Detail Header */}
                <div className="mb-10">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="px-2 py-0.5 border border-neutral-800 font-mono text-[10px] uppercase text-neutral-400">
                      {results.find(r => r.id === selectedRecId).sourceType} Source
                    </span>
                    {safeSourceUrl(results.find(r => r.id === selectedRecId).link) ? (
                      <a href={safeSourceUrl(results.find(r => r.id === selectedRecId).link)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 font-mono text-[10px] uppercase text-blue-400 hover:underline">
                        Verify Origin <IconExternal />
                      </a>
                    ) : <span className="font-mono text-[10px] uppercase text-neutral-600">Origin unavailable</span>}
                  </div>
                  <h2 className="text-3xl text-white font-medium tracking-tight mb-2">
                    {results.find(r => r.id === selectedRecId).name}
                  </h2>
                  <div className="flex gap-8 border-b border-neutral-900 pb-6 mt-6">
                    <div className="flex flex-col">
                      <span className="font-mono text-[10px] text-neutral-500 uppercase mb-1">Funding Profile</span>
                      <span className="text-sm">{results.find(r => r.id === selectedRecId).funding}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="font-mono text-[10px] text-neutral-500 uppercase mb-1">Target Field</span>
                      <span className="text-sm">{results.find(r => r.id === selectedRecId).field}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="font-mono text-[10px] text-neutral-500 uppercase mb-1">Deadline</span>
                      <span className="text-sm font-mono">{results.find(r => r.id === selectedRecId).deadline}</span>
                    </div>
                  </div>
                </div>

                {/* Eligibility Matrix Table */}
                <div>
                  <h3 className="font-mono text-[11px] text-neutral-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <IconDatabase /> System Audit Matrix
                  </h3>
                  <div className="border border-neutral-900 bg-[#0a0a0a]">
                    <div className="grid grid-cols-12 gap-4 border-b border-neutral-900 p-4 bg-[#0d0d0d] font-mono text-[10px] uppercase text-neutral-500 tracking-wider">
                      <div className="col-span-2">Vector</div>
                      <div className="col-span-3">Extracted Req</div>
                      <div className="col-span-3">Profile Data</div>
                      <div className="col-span-4">Audit Output</div>
                    </div>
                    
                    {results.find(r => r.id === selectedRecId).eligibilityMatrix.map((row, idx) => (
                      <div key={idx} className="grid grid-cols-12 gap-4 p-4 border-b border-neutral-900/50 last:border-0 items-start text-sm hover:bg-white/[0.02] transition-colors group">
                        
                        <div className="col-span-2 font-mono text-xs text-neutral-400 mt-1">{row.req}</div>
                        
                        <div className="col-span-3 text-neutral-300 relative">
                          {row.asks}
                          {/* Evidence Tooltip Hover */}
                          <div className="hidden group-hover:block absolute top-full left-0 mt-2 p-3 bg-neutral-900 border border-neutral-700 w-[300px] z-50 shadow-2xl">
                            <div className="font-mono text-[9px] text-neutral-500 uppercase mb-2">Raw Document Extraction:</div>
                            <div className="text-xs text-neutral-300 italic border-l-2 border-neutral-600 pl-2">"{row.quote}"</div>
                          </div>
                        </div>
                        
                        <div className="col-span-3 font-mono text-xs text-neutral-500 mt-1">{row.has}</div>
                        
                        <div className="col-span-4 flex items-start gap-3">
                          {row.decision === 'meets' && <div className="flex items-center gap-1.5 text-emerald-500 font-mono text-[10px] uppercase border border-emerald-900/50 bg-emerald-950/20 px-2 py-1"><IconCheck /> Authorized</div>}
                          {row.decision === 'fails' && <div className="flex items-center gap-1.5 text-red-500 font-mono text-[10px] uppercase border border-red-900/50 bg-red-950/20 px-2 py-1"><IconX /> Rejected</div>}
                          {row.decision === 'unknown' && <div className="flex items-center gap-1.5 text-yellow-500 font-mono text-[10px] uppercase border border-yellow-900/50 bg-yellow-950/20 px-2 py-1"><IconAlert /> Missing Data</div>}
                        </div>

                      </div>
                    ))}
                  </div>
                </div>

              </div>
            )}
          </div>

        </div>
      )}

      {/* Global Scrollbar Style overrides for Chrome/Safari */}
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #262626; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #404040; }
      `}} />
    </div>
  );

  return appState === 'intake' ? renderIntake() : renderDashboard();
}