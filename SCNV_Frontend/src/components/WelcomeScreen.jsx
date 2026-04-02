import { Network, Search, Activity, ChevronRight, CheckCircle2 } from 'lucide-react';
import '../styles/explorer.css';

const AGENTS = [
  { 
    id: 'orchestrator',
    icon: <Network size={20} />,
    iconNode: <Network size={28} strokeWidth={1.5} color="white" />, 
    title: 'Orchestrator Agent', 
    subtitle: 'Coordination',
    desc: 'Routes STO events + user queries, synthesizes findings, and makes final decisions.',
    features: ['Event Routing', 'Query Synthesis', 'Decision Support'],
    color: '#6366f1',
    gradient: 'linear-gradient(135deg, #6366f1 0%, #4338ca 100%)',
    bgColor: '#eef2ff'
  },
  { 
    id: 'analyst',
    icon: <Search size={20} />,
    iconNode: <Search size={28} strokeWidth={1.5} color="white" />, 
    title: 'SCM Analyst Agent',  
    subtitle: 'Classification',
    desc: 'Applies business rules (1–4), performs master data checks, and handles Tier 1 & Tier 2 classification.',
    features: ['Business Rules', 'Master Data Check', 'Tier 1/2 Classification'],
    color: '#8b5cf6',
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)',
    bgColor: '#f5f3ff'
  },
  { 
    id: 'optimizer',
    icon: <Activity size={20} />,
    iconNode: <Activity size={28} strokeWidth={1.5} color="white" />, 
    title: 'Optimizer Agent',    
    subtitle: 'Optimization',
    desc: 'Finds best re-route options, calculates potential savings, and optimizes network flow.',
    features: ['Route Optimization', 'Savings Calculation', 'Flow Analysis'],
    color: '#06b6d4',
    gradient: 'linear-gradient(135deg, #06b6d4 0%, #0369a1 100%)',
    bgColor: '#ecfeff'
  },
];

function WelcomeScreen({ onSelectAgent }) {
  return (
    <div className="explorer-page">
      <div className="explorer-header">
        <div className="explorer-badge">AkzoNobel AI Platform</div>
        <h1 className="explorer-title">Explore Specialized Agents</h1>
        <p className="explorer-subtitle">
          Select an AI agent tailored to your supply chain needs. Each agent provides dedicated intelligence, from workflow coordination to dynamic network optimization.
        </p>
      </div>

      <div className="explorer-grid">
        {AGENTS.map((agent) => (
          <div 
            key={agent.id} 
            className="explorer-card group" 
            onClick={() => onSelectAgent(agent)}
            style={{ background: `linear-gradient(135deg, ${agent.bgColor} 0%, #ffffff 100%)` }}
          >
            {/* Card Background Decoration */}
            <div className="explorer-card__bg" style={{ background: agent.gradient }}></div>
            
            <div className="explorer-card__content">
              {/* Icon Header */}
              <div className="explorer-card__header">
                <div 
                  className="explorer-card__icon-box"
                  style={{ background: agent.gradient, boxShadow: `0 8px 16px -4px ${agent.color}60` }}
                >
                  {agent.iconNode}
                </div>
                <div className="explorer-card__action">
                  <span>Connect</span>
                  <ChevronRight size={16} />
                </div>
              </div>

              {/* Title & Description */}
              <div className="explorer-card__text">
                <div className="explorer-card__subtitle" style={{ color: agent.color }}>
                  {agent.subtitle}
                </div>
                <h3 className="explorer-card__title">{agent.title}</h3>
                <p className="explorer-card__desc">{agent.desc}</p>
              </div>

              {/* Features List */}
              <ul className="explorer-card__features">
                {agent.features.map((feature, idx) => (
                  <li key={idx}>
                    <CheckCircle2 size={16} style={{ color: agent.color }} className="feature-icon" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default WelcomeScreen;
