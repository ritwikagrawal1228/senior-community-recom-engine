
import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { GoogleGenAI, LiveServerMessage, Modality, FunctionDeclaration, Type, Blob } from '@google/genai';
import { CallStatus, ClientProfile, Recommendation, TranscriptionEntry, CallSummary, Community, User, SupportedLanguage } from './types';
import ClientProfileCard from './components/ClientProfileCard';
import RecommendationsCard from './components/RecommendationsCard';
import CallControls from './components/CallControls';
import TranscriptionPanel from './components/TranscriptionPanel';
import SummaryModal from './components/SummaryModal';
import HistoryCard from './components/HistoryCard';
import ComparisonModal from './components/ComparisonModal';
import FeedbackModal from './components/FeedbackModal';
import ProfileSelector from './components/ProfileSelector';
import DatabaseManagementCard from './components/DatabaseManagementCard';
import CommunityFormModal from './components/CommunityFormModal';
import ProcessTextModal from './components/ProcessTextModal';

const updateDashboardFunctionDeclaration: FunctionDeclaration = {
  name: 'updateDashboard',
  description: 'Updates the agent\'s dashboard with the latest client info, recommendations, and guidance.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      clientProfile: {
        type: Type.OBJECT,
        description: 'Object containing extracted client needs. Only include fields for which information has been gathered.',
        properties: {
          name: { type: Type.STRING, description: 'Client\'s full name.' },
          budget: { type: Type.STRING, description: 'Client\'s monthly budget (e.g., "$5000 - $6000")' },
          location: { type: Type.STRING, description: 'Desired city or neighborhood.' },
          careLevel: { type: Type.STRING, description: 'Required level of care (e.g., "Independent Living", "Assisted Living", "Memory Care").' },
          timeline: { type: Type.STRING, description: 'Client\'s move-in timeline (e.g., "Within 3 months").' },
          mobilityNeeds: { type: Type.STRING, description: 'Specific mobility needs (e.g., "Wheelchair accessible", "Walker user").' },
          wheelchairAccessible: { type: Type.BOOLEAN, description: 'Does the client require wheelchair accessibility?' },
          specificDemands: { type: Type.STRING, description: 'Any other specific, unique client requirements or preferences mentioned, such as a private balcony, pet-friendly policies for a large dog, specific dietary needs like kosher meals, etc.' },
        },
        required: [],
      },
      suggestedQuestions: {
        type: Type.ARRAY,
        description: 'A list of 2-3 high-priority questions the agent should ask to gather missing information.',
        items: { type: Type.STRING },
      },
      communityRecommendations: {
        type: Type.ARRAY,
        description: 'A list of top 3 recommended communities based on the current profile. For each, include key details extracted from the knowledge base.',
        items: {
          type: Type.OBJECT,
          properties: {
            name: { type: Type.STRING, description: 'Name of the senior living community.' },
            reason: { type: Type.STRING, description: 'A brief reason why this community is a good match based on the client\'s needs.' },
            price: { type: Type.STRING, description: 'The base price or pricing details, formatted as a string (e.g., "$6000/month" or "Starts at $6,000").' },
            careLevels: { type: Type.ARRAY, description: 'The relevant care levels offered by the community.', items: { type: Type.STRING } },
            amenities: { type: Type.ARRAY, description: 'A list of 2-3 key amenities that are relevant to the client.', items: { type: Type.STRING } },
            address: { type: Type.STRING, description: 'The full street address of the community.' },
            description: { type: Type.STRING, description: 'A brief description of the community.' },
          },
          required: ['name', 'reason', 'price', 'careLevels', 'amenities', 'address', 'description'],
        },
      },
      agentGuidance: {
        type: Type.ARRAY,
        description: 'A list of 2-3 concise, real-time coaching tips for the agent. Examples: "Client mentioned their daughter lives nearby, great rapport-building opportunity!", "Budget seems flexible, probe for potential upsell to a premium suite.", "Clarify if they need a pet-friendly community for their small dog."',
        items: { type: Type.STRING },
      },
    },
    required: ['clientProfile'],
  },
};

// Audio Helper Functions
const encode = (bytes: Uint8Array) => {
  let binary = '';
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
};

const decode = (base64: string) => {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
};

const decodeAudioData = async (
  data: Uint8Array,
  ctx: AudioContext,
  sampleRate: number,
  numChannels: number,
): Promise<AudioBuffer> => {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);

  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) {
      channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
    }
  }
  return buffer;
};


const createBlob = (data: Float32Array): Blob => {
  const l = data.length;
  const int16 = new Int16Array(l);
  for (let i = 0; i < l; i++) {
    int16[i] = data[i] < 0 ? data[i] * 0x8000 : data[i] * 0x7FFF;
  }
  return {
    data: encode(new Uint8Array(int16.buffer)),
    mimeType: 'audio/pcm;rate=16000',
  };
};

export default function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);

  const [callStatus, setCallStatus] = useState<CallStatus>(CallStatus.IDLE);
  const [isAgentAssistMode, setIsAgentAssistMode] = useState(false);
  const [isCallPaused, setIsCallPaused] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<SupportedLanguage>('en');
  const [clientProfile, setClientProfile] = useState<ClientProfile>({});
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [agentGuidance, setAgentGuidance] = useState<string[]>([]);
  const [transcription, setTranscription] = useState<TranscriptionEntry[]>([]);
  const [history, setHistory] = useState<CallSummary[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  
  const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);
  const [isComparisonModalOpen, setIsComparisonModalOpen] = useState(false);
  const [communitiesToCompare, setCommunitiesToCompare] = useState<Community[]>([]);
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);
  const [isCommunityModalOpen, setIsCommunityModalOpen] = useState(false);
  const [communityToEdit, setCommunityToEdit] = useState<Community | null>(null);
  const [isTextModalOpen, setIsTextModalOpen] = useState(false);

  const [summaryText, setSummaryText] = useState('');
  const [view, setView] = useState<'dashboard' | 'database'>('dashboard');

  const sessionRef = useRef<any | null>(null);
  const socketRef = useRef<any | null>(null);
  const inputAudioContextRef = useRef<AudioContext | null>(null);
  const outputAudioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordChunksRef = useRef<BlobPart[]>([]);
  const sourcesRef = useRef(new Set<AudioBufferSourceNode>());
  const nextStartTimeRef = useRef(0);
  const isCallPausedRef = useRef(false);
  const isSessionActiveRef = useRef(false);

  const languageNames = useMemo(() => ({
    en: 'English',
    hi: 'Hindi (हिन्दी)',
    es: 'Spanish (Español)'
  }), []);

  // Map our language codes to Gemini API language codes
  const geminiLanguageCodes = useMemo(() => ({
    en: 'en-US',
    hi: 'hi-IN',
    es: 'es-ES'
  }), []);

  const communitiesListString = useMemo(() => {
    return communities.map(
      c => `- ${c.name} (Location: ${c.location}, Address: ${c.address}, Description: ${c.description}, Care: ${c.careLevels.join('/')}, Price: ${c.pricingDetails}, Amenities: [${c.amenities.join(', ')}], Partner: ${c.isPartner ? 'Yes' : 'No'}, Wheelchair Accessible: ${c.wheelchairAccessible}, Availability: ${c.availability})`
    ).join('\n');
  }, [communities]);

  const ACTIVE_AI_SYSTEM_INSTRUCTION = useMemo(() => `You are the "AI Senior Living Sales Assistant," a sophisticated AI partner for a senior living placement consultant on a live call. Your primary role is to actively guide the conversation, ask clarifying questions, and provide verbal suggestions to help the consultant. While you speak, you MUST also use the 'updateDashboard' function to keep the consultant's dashboard updated in real-time.

**CRITICAL LANGUAGE REQUIREMENT: You must ONLY listen to, transcribe, and respond in ${languageNames[selectedLanguage]}. Completely ignore any speech that is not in ${languageNames[selectedLanguage]}. All your responses, questions, and dashboard updates must be exclusively in ${languageNames[selectedLanguage]}.**

**Core Directives:**
1.  **Be a Proactive Conversationalist:** Don't just listen. Your first goal is to politely ask for and capture the client's name. Actively participate. If the client mentions a need, verbally acknowledge it and naturally flow to the next topic. Keep your responses conversational and avoid repeating questions you've already asked.
2.  **Speak and Update Simultaneously:** As you process the conversation, generate helpful spoken responses for the consultant AND call the \`updateDashboard\` function ONCE per turn when you have new information. For example, if the client says "I need a place in Sunnyvale," you should say something like, "Okay, Sunnyvale is a great area. What's your budget looking like for that location?" while calling \`updateDashboard\` with the location "Sunnyvale."
3.  **Real-time Dashboard Management:**
    *   **Extract & Update Instantly**: The moment you identify NEW details (name, location, budget, care needs, accessibility needs, or other specific demands), call \`updateDashboard\` to populate the \`clientProfile\`. Only call updateDashboard when you have genuinely new information to share.
    *   **Suggest Questions Dynamically**: Update \`suggestedQuestions\` with 2-3 high-priority questions that haven't been answered yet. Don't repeat questions the client has already answered.
    *   **Generate & Refine Recommendations Wisely**: Generate initial recommendations when you have enough information (at least location OR care level). Refine recommendations when you learn significant new details (budget change, care level clarification, mobility requirements). Don't update recommendations for minor conversation filler. Prioritize: location, budget, wheelchair accessibility, partner status, and 'Immediate' availability for urgent timelines.

**Available Communities Knowledge Base (Simulating ~50,000 facilities):**
${communitiesListString}`, [selectedLanguage, languageNames, communitiesListString]);

const AGENT_ASSIST_SYSTEM_INSTRUCTION = useMemo(() => `You are the "AI Senior Living Sales Assistant" in **Agent Assist Mode**. You are a silent partner for a human consultant on a live call. Your primary role is to listen to the client and provide text-based guidance, suggestions, and data points to the human consultant on their dashboard. **You MUST NOT generate any spoken audio response.**

**CRITICAL LANGUAGE REQUIREMENT: You must ONLY listen to and transcribe speech in ${languageNames[selectedLanguage]}. Completely ignore any speech that is not in ${languageNames[selectedLanguage]}. All your text-based guidance and dashboard updates must be exclusively in ${languageNames[selectedLanguage]}.**

**Core Directives:**
1.  **Listen and Analyze:** Transcribe the client's speech accurately.
2.  **Provide Text Guidance:** Instead of speaking, your output will be text-only suggestions for the agent. This includes:
    *   **Update Dashboard:** Use the 'updateDashboard' function when you have NEW information to share. Only call it when there are genuine updates, not on every message.
    *   **Provide Actionable Guidance:** Offer 2-3 concise coaching tips via \`agentGuidance\`. Identify opportunities for upselling, rapport building, or clarifying inconsistencies. Examples: "Client mentioned their daughter lives nearby, great rapport-building opportunity!" or "Budget seems flexible, probe for potential upsell to a premium suite."
    *   **Suggest Questions:** Provide 2-3 high-priority unanswered questions via \`suggestedQuestions\`. Don't repeat questions the client has already answered.
3.  **Generate & Refine Recommendations Wisely**: Generate initial recommendations when you have enough information (at least location OR care level). Refine recommendations when you learn significant new details (budget change, care level clarification, mobility requirements). Don't update recommendations for minor conversation filler. Prioritize: location, budget, wheelchair accessibility, partner status, and 'Immediate' availability for urgent timelines.
4.  **Be Concise:** Keep your text guidance brief and to the point. The agent is on a live call and needs information quickly.

**Available Communities Knowledge Base (Simulating ~50,000 facilities):**
${communitiesListString}`, [selectedLanguage, languageNames, communitiesListString]);

  const fetchCommunities = useCallback(async () => {
    try {
      const response = await fetch('/api/communities');
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      const mappedCommunities = data.communities.map((c: any) => ({
        id: c.CommunityID,
        name: `Community ${c.CommunityID}`,
        location: `ZIP ${c.ZIP}`,
        address: `${c.ZIP}, USA`,
        description: `A community offering ${c['Care Level']}`,
        careLevels: c['Care Level'] ? [c['Care Level']] : [],
        basePrice: c['Monthly Fee'] || 0,
        pricingDetails: `Starts at $${c['Monthly Fee'] || 0}`,
        isPartner: c['Work with Placement?'] === 'Yes',
        amenities: [], // This data is not in the excel file
        lat: 0, // This data is not in the excel file
        lng: 0, // This data is not in the excel file
        wheelchairAccessible: true, // Assuming default
        hasKitchen: false, // Assuming default
        availability: c['Est. Waitlist Length'] === 'Available' ? 'Immediate' : 'Waitlist',
      }));
      setCommunities(mappedCommunities);
    } catch (error) {
      console.error("Failed to fetch communities:", error);
      alert('Error: Could not load community data from the backend.');
    }
  }, []);


  

  useEffect(() => {
    if (currentUser) {
      setIsHistoryLoading(true);
      fetchCommunities().then(() => {
        setIsHistoryLoading(false);
      });
      // Mock history fetching is removed, CRM will handle history.
      setHistory([]); 
    } else {
      setHistory([]);
    }
  }, [currentUser, fetchCommunities]);

  const handleLogin = (user: User) => {
    setCurrentUser(user);
    resetState();
  };
  
  const handleLogout = () => {
    setCurrentUser(null);
    setView('dashboard');
  };

  const resetState = () => {
      setClientProfile({});
      setRecommendations([]);
      setSuggestedQuestions([]);
      setAgentGuidance([]);
      setTranscription([]);
      setIsAgentAssistMode(false);
  }

  const generateSummaryText = (): string => {
    let summary = `Call Summary - ${new Date().toLocaleString()}\n\n`;

    summary += '--- CLIENT PROFILE ---\n';
    if (Object.keys(clientProfile).length > 0) {
      summary += `Name: ${clientProfile.name || 'Not specified'}\n`;
      summary += `Budget: ${clientProfile.budget || 'Not specified'}\n`;
      summary += `Location: ${clientProfile.location || 'Not specified'}\n`;
      summary += `Care Level: ${clientProfile.careLevel || 'Not specified'}\n`;
      summary += `Timeline: ${clientProfile.timeline || 'Not specified'}\n`;
      summary += `Mobility Needs: ${clientProfile.mobilityNeeds || 'Not specified'}\n`;
      let wheelchairStatus = 'Not specified';
      if (clientProfile.wheelchairAccessible === true) {
        wheelchairStatus = 'Yes';
      } else if (clientProfile.wheelchairAccessible === false) {
        wheelchairStatus = 'No';
      }
      summary += `Wheelchair Accessible: ${wheelchairStatus}\n`;
      summary += `Specific Demands: ${clientProfile.specificDemands || 'Not specified'}\n`;
    } else {
      summary += 'No client profile information was gathered.\n';
    }

    summary += '\n--- FINAL RECOMMENDATIONS ---\n';
    if (recommendations.length > 0) {
      recommendations.forEach((rec, index) => {
        summary += `${index + 1}. ${rec.name}\n`;
        summary += `   - Reason: ${rec.reason}\n`;
        summary += `   - Price: ${rec.price}\n`;
        summary += `   - Address: ${rec.address}\n`;
        summary += `   - Description: ${rec.description}\n`;
        summary += `   - Care Levels: ${rec.careLevels?.join(', ')}\n`;
        summary += `   - Key Amenities: ${rec.amenities?.join(', ')}\n\n`;
      });
    } else {
      summary += 'No final recommendations were provided.\n';
    }
    
    return summary;
  };

  const handleSaveSummary = async () => {
    if (!currentUser) return;
    const text = generateSummaryText();
    setSummaryText(text);
    setIsSummaryModalOpen(true);
    // History is now managed by CRM, but we can keep a temporary session history if needed.
    // For now, saving to local state for viewing purposes.
    const newSummary: CallSummary = { date: new Date().toISOString(), summary: text };
    setHistory(prev => [newSummary, ...prev]);
  };
  
  const handleCloseSummaryModal = () => {
    setIsSummaryModalOpen(false);
    setSummaryText('');
  };

  const handleViewHistorySummary = (summary: string) => {
    setSummaryText(summary);
    setIsSummaryModalOpen(true);
  };

  const handleOpenComparisonModal = (selectedCommunities: Community[]) => {
    setCommunitiesToCompare(selectedCommunities);
    setIsComparisonModalOpen(true);
  };
  const handleCloseComparisonModal = () => setIsComparisonModalOpen(false);

  const handleOpenFeedbackModal = () => setIsFeedbackModalOpen(true);
  const handleCloseFeedbackModal = () => setIsFeedbackModalOpen(false);


  const handleStartCall = useCallback(async (isAssistMode = false) => {
    if(!isAssistMode) {
        resetState();
    }
    setIsCallPaused(false);
    isCallPausedRef.current = false;
    setCallStatus(CallStatus.CONNECTING);
    setIsAgentAssistMode(isAssistMode);

    try {
      // Use Gemini SDK directly like Google Studio
      const apiKey = (window as any).GEMINI_API_KEY
        || (document.querySelector('meta[name="gemini-api-key"]') as HTMLMetaElement)?.content
        || (process as any)?.env?.GEMINI_API_KEY;
      
      console.log('========================================');
      console.log('🔑 GEMINI API KEY CHECK');
      console.log('========================================');
      console.log('API Key found:', apiKey ? '✅ YES' : '❌ NO');
      if (apiKey) {
        console.log('API Key length:', apiKey.length);
        console.log('API Key (first 10 chars):', apiKey.substring(0, 10) + '...');
        console.log('API Key (last 10 chars):', '...' + apiKey.substring(apiKey.length - 10));
      }
      console.log('========================================');
      
      if (!apiKey) {
        throw new Error("API key not available");
      }
      
      console.log('[DEBUG] Creating GoogleGenAI client...');
      const ai = new GoogleGenAI({ apiKey });
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      inputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      outputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      
      const systemInstruction = isAssistMode ? AGENT_ASSIST_SYSTEM_INSTRUCTION : ACTIVE_AI_SYSTEM_INSTRUCTION;

      console.log(`[DEBUG] Configuring Gemini with language: ${selectedLanguage} (${geminiLanguageCodes[selectedLanguage]})`);

      const sessionPromise = ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
        config: {
          responseModalities: [Modality.AUDIO],
          inputAudioTranscription: {
            languageCode: geminiLanguageCodes[selectedLanguage],
          },
          outputAudioTranscription: {
            languageCode: geminiLanguageCodes[selectedLanguage],
          },
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: {
                voiceName: selectedLanguage === 'en' ? 'Puck' : selectedLanguage === 'hi' ? 'Sage' : 'Aoede'
              }
            },
            languageCode: geminiLanguageCodes[selectedLanguage],
          },
          tools: [{ functionDeclarations: [updateDashboardFunctionDeclaration] }],
          systemInstruction: systemInstruction,
        },
        callbacks: {
          onopen: () => {
            console.log('[DEBUG] Session opened, setting up audio...');
            // Session will be set from the promise below, just mark as active
            setCallStatus(CallStatus.ACTIVE);
            const source = inputAudioContextRef.current!.createMediaStreamSource(stream);
            const scriptProcessor = inputAudioContextRef.current!.createScriptProcessor(4096, 1, 1);
            processorRef.current = scriptProcessor;

            scriptProcessor.onaudioprocess = (audioProcessingEvent) => {
              if (isCallPausedRef.current) return;
              if (!isSessionActiveRef.current || !sessionRef.current) {
                return; // Session not active or closed
              }
              const inputData = audioProcessingEvent.inputBuffer.getChannelData(0);
              const pcmBlob = createBlob(inputData);
              try {
                if (isSessionActiveRef.current && sessionRef.current) {
                  sessionRef.current.sendRealtimeInput({ media: pcmBlob });
                }
              } catch (error: any) {
                // Silently handle WebSocket closed errors
                if (error?.message?.includes('CLOSING') || error?.message?.includes('CLOSED')) {
                  isSessionActiveRef.current = false;
                  return;
                }
                console.debug('[DEBUG] Could not send audio:', error);
              }
            };
            source.connect(scriptProcessor);
            scriptProcessor.connect(inputAudioContextRef.current!.destination);
            console.log('[DEBUG] Audio processing ready');
          },
          onmessage: async (message: LiveServerMessage) => {
            console.log('[DEBUG] Received message:', message);
            if(message.toolCall?.functionCalls) {
              for (const fc of message.toolCall.functionCalls) {
                if(fc.name === 'updateDashboard' && fc.args) {
                    const { clientProfile: newProfile, suggestedQuestions: newQuestions, communityRecommendations: newRecs, agentGuidance: newGuidance } = fc.args as any;
                    
                    setClientProfile(prev => ({...prev, ...(newProfile || {})}));
                    if(newQuestions) {
                        setSuggestedQuestions(newQuestions);
                    }
                    if(newRecs) {
                        setRecommendations(newRecs);
                    }
                    if (newGuidance) {
                        setAgentGuidance(newGuidance);
                    }

                    if (sessionRef.current) {
                      try {
                        sessionRef.current.sendToolResponse({
                          functionResponses: {
                            id: fc.id,
                            name: fc.name,
                            response: { result: "Dashboard updated successfully." }
                          }
                        });
                      } catch (error) {
                        console.debug('[DEBUG] Could not send tool response:', error);
                      }
                    }
                }
              }
            }
            if(message.serverContent?.inputTranscription) {
                const text = message.serverContent.inputTranscription.text;
                if (text && text.trim().length > 0) {
                  console.log('[DEBUG] Input transcription:', text);
                  setTranscription(prev => {
                      const last = prev[prev.length - 1];
                      // Only append if it's the same speaker and the text is actually new
                      if(last?.speaker === 'user' && !last.text.includes(text)) {
                          return [...prev.slice(0, -1), {speaker: 'user', text: last.text + ' ' + text}];
                      } else if (last?.speaker === 'user' && last.text.includes(text)) {
                          // Duplicate, skip it
                          return prev;
                      }
                      return [...prev, {speaker: 'user', text}];
                  });
                }
            }
             if (message.serverContent?.outputTranscription) {
                const text = message.serverContent.outputTranscription.text;
                if (text && text.trim().length > 0) {
                  console.log('[DEBUG] Output transcription:', text);
                  setTranscription(prev => {
                      const last = prev[prev.length - 1];
                      // Only append if it's the same speaker and the text is actually new
                      if(last?.speaker === 'model' && !last.text.includes(text)) {
                          return [...prev.slice(0, -1), {speaker: 'model', text: last.text + ' ' + text}];
                      } else if (last?.speaker === 'model' && last.text.includes(text)) {
                          // Duplicate, skip it
                          return prev;
                      }
                      return [...prev, {speaker: 'model', text}];
                  });
                }
            }
             const base64Audio = message.serverContent?.modelTurn?.parts[0]?.inlineData?.data;
              if (!isAgentAssistMode && base64Audio && outputAudioContextRef.current) {
                const outputAudioContext = outputAudioContextRef.current;
                nextStartTimeRef.current = Math.max(nextStartTimeRef.current, outputAudioContext.currentTime);

                const audioBuffer = await decodeAudioData(decode(base64Audio), outputAudioContext, 24000, 1);

                const source = outputAudioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(outputAudioContext.destination);

                source.addEventListener('ended', () => {
                  sourcesRef.current.delete(source);
                });

                source.start(nextStartTimeRef.current);
                nextStartTimeRef.current += audioBuffer.duration;
                sourcesRef.current.add(source);
              }

              if (message.serverContent?.interrupted) {
                for (const source of sourcesRef.current.values()) {
                  source.stop();
                  sourcesRef.current.delete(source);
                }
                nextStartTimeRef.current = 0;
              }
          },
          onerror: (e: ErrorEvent) => {
            console.error('[DEBUG] Session error:', e);
            isSessionActiveRef.current = false;
            setCallStatus(CallStatus.ERROR);
            handleEndCall();
          },
          onclose: () => {
            console.log('[DEBUG] Session closed.');
            isSessionActiveRef.current = false;
          },
        },
      });
      console.log('[DEBUG] Session promise created, waiting for connection...');
      // Wait for session to be ready and store it
      const session = await sessionPromise;
      sessionRef.current = session;
      isSessionActiveRef.current = true;
      console.log('[DEBUG] Session promise resolved, session stored');
    } catch (error) {
      console.error('[DEBUG] Failed to start call:', error);
      setCallStatus(CallStatus.ERROR);
      alert(`Failed to start call: ${error instanceof Error ? error.message : String(error)}`);
    }
  }, [ACTIVE_AI_SYSTEM_INSTRUCTION, AGENT_ASSIST_SYSTEM_INSTRUCTION, selectedLanguage, geminiLanguageCodes]);

  // OLD CODE - KEEP FOR FALLBACK IF NEEDED
  const handleStartCallOLD = useCallback(async (isAssistMode = false) => {
    if(!isAssistMode) {
        resetState();
    }
    setIsCallPaused(false);
    isCallPausedRef.current = false;
    setCallStatus(CallStatus.CONNECTING);
    setIsAgentAssistMode(isAssistMode);

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      inputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      outputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      
      const systemInstruction = isAssistMode ? AGENT_ASSIST_SYSTEM_INSTRUCTION : ACTIVE_AI_SYSTEM_INSTRUCTION;

      const sessionPromise = ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
        config: {
          responseModalities: [Modality.AUDIO],
          inputAudioTranscription: {},
          outputAudioTranscription: {},
          tools: [{ functionDeclarations: [updateDashboardFunctionDeclaration] }],
          systemInstruction: systemInstruction,
        },
        callbacks: {
          onopen: () => {
            setCallStatus(CallStatus.ACTIVE);
            const source = inputAudioContextRef.current!.createMediaStreamSource(stream);
            const scriptProcessor = inputAudioContextRef.current!.createScriptProcessor(4096, 1, 1);
            processorRef.current = scriptProcessor;

            scriptProcessor.onaudioprocess = (audioProcessingEvent) => {
              if (isCallPausedRef.current) return;
              if (!sessionRef.current) return; // Session closed
              const inputData = audioProcessingEvent.inputBuffer.getChannelData(0);
              const pcmBlob = createBlob(inputData);
              sessionPromise.then((session) => {
                  if (sessionRef.current && session === sessionRef.current) {
                    try {
                      session.sendRealtimeInput({ media: pcmBlob });
                    } catch (error) {
                      // Session might be closed, ignore
                      console.debug('Could not send audio (session closed):', error);
                    }
                  }
              }).catch(() => {
                // Session closed, ignore
              });
            };
            source.connect(scriptProcessor);
            scriptProcessor.connect(inputAudioContextRef.current!.destination);
          },
          onmessage: async (message: LiveServerMessage) => {
            console.log('[DEBUG] Received message:', message);
            if(message.toolCall?.functionCalls) {
              for (const fc of message.toolCall.functionCalls) {
                if(fc.name === 'updateDashboard' && fc.args) {
                    const { clientProfile: newProfile, suggestedQuestions: newQuestions, communityRecommendations: newRecs, agentGuidance: newGuidance } = fc.args as any;
                    
                    setClientProfile(prev => ({...prev, ...(newProfile || {})}));
                    if(newQuestions) {
                        setSuggestedQuestions(newQuestions);
                    }
                    if(newRecs) {
                        setRecommendations(newRecs);
                    }
                    if (newGuidance) {
                        setAgentGuidance(newGuidance);
                    }

                    if (sessionRef.current) {
                      try {
                        sessionRef.current.sendToolResponse({
                          functionResponses: {
                            id: fc.id,
                            name: fc.name,
                            response: { result: "Dashboard updated successfully." }
                          }
                        });
                      } catch (error) {
                        console.debug('[DEBUG] Could not send tool response:', error);
                      }
                    }
                }
              }
            }
            if(message.serverContent?.inputTranscription) {
                const text = message.serverContent.inputTranscription.text;
                if (text && text.trim().length > 0) {
                  console.log('[DEBUG] Input transcription:', text);
                  setTranscription(prev => {
                      const last = prev[prev.length - 1];
                      // Only append if it's the same speaker and the text is actually new
                      if(last?.speaker === 'user' && !last.text.includes(text)) {
                          return [...prev.slice(0, -1), {speaker: 'user', text: last.text + ' ' + text}];
                      } else if (last?.speaker === 'user' && last.text.includes(text)) {
                          // Duplicate, skip it
                          return prev;
                      }
                      return [...prev, {speaker: 'user', text}];
                  });
                }
            }
             if (message.serverContent?.outputTranscription) {
                const text = message.serverContent.outputTranscription.text;
                if (text && text.trim().length > 0) {
                  console.log('[DEBUG] Output transcription:', text);
                  setTranscription(prev => {
                      const last = prev[prev.length - 1];
                      // Only append if it's the same speaker and the text is actually new
                      if(last?.speaker === 'model' && !last.text.includes(text)) {
                          return [...prev.slice(0, -1), {speaker: 'model', text: last.text + ' ' + text}];
                      } else if (last?.speaker === 'model' && last.text.includes(text)) {
                          // Duplicate, skip it
                          return prev;
                      }
                      return [...prev, {speaker: 'model', text}];
                  });
                }
            }
             const base64Audio = message.serverContent?.modelTurn?.parts[0]?.inlineData?.data;
              if (!isAgentAssistMode && base64Audio && outputAudioContextRef.current) {
                const outputAudioContext = outputAudioContextRef.current;
                nextStartTimeRef.current = Math.max(nextStartTimeRef.current, outputAudioContext.currentTime);

                const audioBuffer = await decodeAudioData(decode(base64Audio), outputAudioContext, 24000, 1);

                const source = outputAudioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(outputAudioContext.destination);

                source.addEventListener('ended', () => {
                  sourcesRef.current.delete(source);
                });

                source.start(nextStartTimeRef.current);
                nextStartTimeRef.current += audioBuffer.duration;
                sourcesRef.current.add(source);
              }

              if (message.serverContent?.interrupted) {
                for (const source of sourcesRef.current.values()) {
                  source.stop();
                  sourcesRef.current.delete(source);
                }
                nextStartTimeRef.current = 0;
              }
          },
          onerror: (e: ErrorEvent) => {
            console.error('Session error:', e);
            setCallStatus(CallStatus.ERROR);
            handleEndCall();
          },
          onclose: () => {
            console.log('Session closed.');
          },
        },
      });
      sessionRef.current = await sessionPromise;

    } catch (error) {
      console.error('Failed to start call (OLD):', error);
      setCallStatus(CallStatus.ERROR);
    }
  }, [ACTIVE_AI_SYSTEM_INSTRUCTION, AGENT_ASSIST_SYSTEM_INSTRUCTION]);

  

  const processBackendConsultation = useCallback(async (data: { text?: string; audio?: File }) => {
    resetState();
    setCallStatus(CallStatus.PROCESSING);

    try {
      let response;
      if (data.text) {
        setTranscription([{ speaker: 'user', text: data.text }]);
        response = await fetch('/api/process-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: data.text, push_to_crm: true }),
        });
      } else if (data.audio) {
        setTranscription([{ speaker: 'user', text: `Processing audio file: ${data.audio.name}` }]);
        const formData = new FormData();
        formData.append('audio', data.audio);
        formData.append('push_to_crm', 'true');
        response = await fetch('/api/process-audio', {
          method: 'POST',
          body: formData,
        });
      } else {
        throw new Error('No data provided to process.');
      }

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Backend processing failed.');
      }

      const result = await response.json();
      
      // Update UI with results from backend
      const clientInfo = result.client_info || {};
      setClientProfile({
          name: clientInfo.client_name,
          budget: clientInfo.budget ? `$${clientInfo.budget}` : undefined,
          location: clientInfo.location_preference,
          careLevel: clientInfo.care_level,
          timeline: clientInfo.timeline,
          // Map other fields as necessary
      });

      const backendRecommendations = result.recommendations || [];
      const formattedRecommendations = backendRecommendations.map((r: any) => ({
          name: r.community_name || `Community ${r.community_id}`,
          reason: r.explanations?.holistic_reason || 'No reason provided.',
          price: r.key_metrics?.monthly_fee ? `$${r.key_metrics.monthly_fee.toLocaleString()}`: 'N/A',
          address: `ZIP: ${r.key_metrics?.zip_code || 'N/A'}`,
          description: `A good match based on the analysis.`,
          careLevels: [r.key_metrics?.care_level],
          amenities: [], // This info is not in the backend response
      }));
      setRecommendations(formattedRecommendations);

    } catch (error: any) {
      console.error("Failed to process consultation:", error);
      setCallStatus(CallStatus.ERROR);
      alert(`Error: ${error.message}`);
    } finally {
      setCallStatus(CallStatus.IDLE);
    }
  }, []);

  const handleAudioFileSelect = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    await processBackendConsultation({ audio: file });
    if (event.target) event.target.value = ''; // Reset file input
  }, [processBackendConsultation]);

  const handleProcessText = useCallback(async (text: string) => {
    if (!text.trim()) return;
    await processBackendConsultation({ text });
  }, [processBackendConsultation]);

  const handleEndCall = useCallback((setIdleOnEnd = true) => {
    // Mark session as inactive FIRST to prevent new sends
    isSessionActiveRef.current = false;
    
    // Disconnect processor to stop audio processing before closing session
    if(processorRef.current) {
        processorRef.current.disconnect();
        processorRef.current = null;
    }
    // Then close the session
    if (sessionRef.current) {
      try {
        sessionRef.current.close();
      } catch (error) {
        // Session might already be closed, ignore
        console.debug('[DEBUG] Session already closed:', error);
      }
      sessionRef.current = null;
    }
    if (inputAudioContextRef.current && inputAudioContextRef.current.state !== 'closed') {
      inputAudioContextRef.current.close();
      inputAudioContextRef.current = null;
    }
    if (outputAudioContextRef.current && outputAudioContextRef.current.state !== 'closed') {
      outputAudioContextRef.current.close();
      outputAudioContextRef.current = null;
    }
    if(mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
        mediaStreamRef.current = null;
    }
    sourcesRef.current.forEach(source => source.stop());
    sourcesRef.current.clear();
    nextStartTimeRef.current = 0;
    
    setIsCallPaused(false);
    isCallPausedRef.current = false;
    
    if (setIdleOnEnd) {
      setCallStatus(CallStatus.IDLE);
    }
  }, []);
  
  const handleTogglePause = useCallback(() => {
    if (callStatus !== CallStatus.ACTIVE) return;

    const newPausedState = !isCallPausedRef.current;
    isCallPausedRef.current = newPausedState;
    setIsCallPaused(newPausedState);

    if (newPausedState) {
        // When pausing, stop any currently playing AI audio.
        if (outputAudioContextRef.current) {
            sourcesRef.current.forEach(source => source.stop());
            sourcesRef.current.clear();
            nextStartTimeRef.current = 0;
        }
    }
  }, [callStatus]);

  const handleToggleAssistMode = useCallback(() => {
    if (callStatus !== CallStatus.ACTIVE) return;
    const newMode = !isAgentAssistMode;
    handleEndCall(false); 
    handleStartCall(newMode);
  }, [callStatus, isAgentAssistMode, handleEndCall, handleStartCall]);
  
  const handleForceRecommendationUpdate = useCallback(() => {
    if (callStatus !== CallStatus.ACTIVE) return;
    handleEndCall(false); 
    handleStartCall(isAgentAssistMode);
  }, [callStatus, isAgentAssistMode, handleEndCall, handleStartCall]);

  const handleEscalateCall = () => {
    alert('Call escalated! A manager has been notified and will join shortly.');
  };

  const handleOpenCommunityModal = (community: Community | null) => {
    setCommunityToEdit(community);
    setIsCommunityModalOpen(true);
  }

  const handleCloseCommunityModal = () => {
    setCommunityToEdit(null);
    setIsCommunityModalOpen(false);
  }

  const handleSaveCommunity = async (communityData: Omit<Community, 'id'>) => {
    const url = communityToEdit ? `/api/communities/${communityToEdit.id}` : '/api/communities';
    const method = communityToEdit ? 'PUT' : 'POST';
    
    // Map frontend Community type to backend Excel format
    const backendData = {
        "Name": communityData.name,
        "Care Level": communityData.careLevels[0],
        "Monthly Fee": communityData.basePrice,
        "ZIP": communityData.location.replace('ZIP ', ''),
        "Work with Placement?": communityData.isPartner,
        "Est. Waitlist Length": communityData.availability,
    };

    try {
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(backendData)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to save community');
        }
        await fetchCommunities(); // Refresh data
        handleCloseCommunityModal();
    } catch (error: any) {
        alert(`Error saving community: ${error.message}`);
    }
  };
  
  const handleDeleteCommunity = async (communityId: number) => {
    if(window.confirm(`Are you sure you want to delete community #${communityId}? This action cannot be undone.`)) {
        try {
            const response = await fetch(`/api/communities/${communityId}`, { method: 'DELETE' });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Failed to delete community');
            }
            await fetchCommunities(); // Refresh data
        } catch (error: any) {
             alert(`Error deleting community: ${error.message}`);
        }
    }
  };


  if (!currentUser) {
    return <ProfileSelector onSelectProfile={handleLogin} />;
  }

  const NavButton: React.FC<{
    targetView: 'dashboard' | 'database';
    label: string;
    icon: React.ReactNode;
  }> = ({ targetView, label, icon }) => (
    <button
      onClick={() => setView(targetView)}
      className={`px-3 py-2 text-sm font-semibold rounded-md flex items-center gap-2 transition-colors ${
        view === targetView
          ? 'bg-blue-100 text-blue-600'
          : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      {icon}
      {label}
    </button>
  );

  return (
    <div className="min-h-screen font-sans text-gray-800 bg-[#F8F7F2] flex flex-col">
      <header className="bg-[rgba(255,255,255,0.7)] backdrop-blur-lg sticky top-0 z-20 border-b border-gray-200">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-3">
                 <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-3">
                      <svg className="w-8 h-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1.28 15.58L6.5 13.36l1.41-1.41 2.81 2.81 6.22-6.22 1.41 1.41-7.63 7.63z"></path></svg>
                      <h1 className="text-xl font-bold text-gray-800 tracking-tight">AI Sales Assistant</h1>
                    </div>
                     <div className="flex items-center bg-gray-100/80 rounded-lg p-1 space-x-1">
                        <NavButton 
                          targetView="dashboard" 
                          label="Live Dashboard" 
                          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" /></svg>}
                        />
                        <NavButton 
                          targetView="database" 
                          label="Community Database"
                          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M3 3a1 1 0 000 2h14a1 1 0 100-2H3zM3 7a1 1 0 000 2h14a1 1 0 100-2H3zM3 11a1 1 0 000 2h14a1 1 0 100-2H3zM3 15a1 1 0 000 2h14a1 1 0 100-2H3z" /></svg>}
                        />
                     </div>
                 </div>
                 <div className="flex items-center space-x-4">
                    <CallControls 
                        status={callStatus} 
                        isAgentAssistMode={isAgentAssistMode}
                        isCallPaused={isCallPaused}
                        selectedLanguage={selectedLanguage}
                        onLanguageChange={setSelectedLanguage}
                        onStart={() => handleStartCall(false)} 
                        onEnd={() => handleEndCall()}
                        onToggleAssistMode={handleToggleAssistMode}
                        onTogglePause={handleTogglePause}
                        onForceUpdate={handleForceRecommendationUpdate}
                        onEscalate={handleEscalateCall}
                        onSaveSummary={handleSaveSummary}
                        onAudioFileSelect={handleAudioFileSelect}
                        onProcessText={() => setIsTextModalOpen(true)}
                        hasData={Object.keys(clientProfile).length > 0 || recommendations.length > 0}
                    />
                    <div className="h-8 w-px bg-gray-200"></div>
                    <div className="flex items-center space-x-3">
                         <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center border-2 border-blue-200">
                             <span className="text-md font-bold text-blue-600">{currentUser.avatar}</span>
                         </div>
                         <div>
                            <p className="text-sm font-semibold text-gray-800">{currentUser.name}</p>
                            <p className="text-xs text-gray-500">{currentUser.title}</p>
                         </div>
                         <button onClick={handleLogout} title="Log Out" className="p-2 rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                         </button>
                    </div>
                 </div>
            </div>
        </div>
      </header>
    
      <main className="flex-grow max-w-screen-2xl mx-auto p-4 sm:p-6 lg:p-8 w-full flex flex-col gap-6">
        {view === 'dashboard' ? (
            <>
                {/* Top Row: Recommendations */}
                <div className="w-full">
                    <RecommendationsCard 
                    recommendations={recommendations}
                    allCommunities={communities}
                    onCompare={handleOpenComparisonModal}
                    />
                </div>

                {/* Bottom Row: Info Hub */}
                <div className="w-full grid grid-cols-12 gap-6 flex-grow min-h-0">
                    {/* Left Panel - Profile */}
                    <div className="col-span-12 lg:col-span-4">
                        <ClientProfileCard profile={clientProfile} />
                    </div>

                    {/* Center Panel - Conversation */}
                    <div className="col-span-12 lg:col-span-6 h-full min-h-0">
                        <TranscriptionPanel 
                            entries={transcription} 
                            clientProfile={clientProfile} 
                            suggestedQuestions={suggestedQuestions}
                            agentGuidance={agentGuidance}
                            isAgentAssistMode={isAgentAssistMode}
                            communities={communities}
                        />
                    </div>
                    
                    {/* Right Panel - History */}
                    <div className="col-span-12 lg:col-span-2">
                        <HistoryCard history={history} onViewSummary={handleViewHistorySummary} isLoading={isHistoryLoading} />
                    </div>
                </div>
            </>
        ) : (
            <DatabaseManagementCard
                communities={communities}
                onAdd={() => handleOpenCommunityModal(null)}
                onEdit={(community) => handleOpenCommunityModal(community)}
                onDelete={handleDeleteCommunity}
            />
        )}
      </main>

      <SummaryModal 
        isOpen={isSummaryModalOpen}
        onClose={handleCloseSummaryModal}
        summaryText={summaryText}
      />
      <ComparisonModal
        isOpen={isComparisonModalOpen}
        onClose={handleCloseComparisonModal}
        communities={communitiesToCompare}
      />
       <FeedbackModal
        isOpen={isFeedbackModalOpen}
        onClose={handleCloseFeedbackModal}
      />
      <CommunityFormModal
        isOpen={isCommunityModalOpen}
        onClose={handleCloseCommunityModal}
        onSubmit={handleSaveCommunity}
        communityToEdit={communityToEdit}
      />
      <ProcessTextModal
        isOpen={isTextModalOpen}
        onClose={() => setIsTextModalOpen(false)}
        onSubmit={handleProcessText}
      />

      {/* Feedback Button */}
      <button
        onClick={handleOpenFeedbackModal}
        className="fixed bottom-6 right-6 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#F8F7F2] focus:ring-blue-500 z-30"
        aria-label="Provide Feedback"
        title="Provide Feedback"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>
    </div>
  );
}