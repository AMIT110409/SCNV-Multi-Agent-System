import React from 'react';
import { Network, Search, Activity } from 'lucide-react';

export const AGENTS = [
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
