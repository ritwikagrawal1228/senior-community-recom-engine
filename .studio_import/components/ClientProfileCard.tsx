

import React from 'react';
import { ClientProfile } from '../types';

interface ClientProfileCardProps {
  profile: ClientProfile;
}

// FIX: Changed icon type from JSX.Element to React.ReactNode to resolve namespace error.
const ProfileField: React.FC<{ label: string; value?: string | boolean; icon: React.ReactNode }> = ({ label, value, icon }) => {
    let displayValue: string;
    let isSet: boolean;

    if (typeof value === 'boolean') {
        displayValue = value ? 'Yes' : 'No';
        isSet = true;
    } else {
        displayValue = value || '';
        isSet = !!value;
    }
    
    return (
      <div className={`p-3 rounded-lg transition-all duration-300 flex items-center space-x-4 ${isSet ? 'bg-blue-50' : 'bg-gray-100'}`}>
         <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${isSet ? 'bg-blue-100 text-blue-500' : 'bg-gray-200 text-gray-500'}`}>
            {icon}
        </div>
        <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{label}</h3>
            {isSet ? (
            <p className="text-md font-semibold text-gray-800">{displayValue}</p>
            ) : (
            <p className="text-sm text-gray-400 italic">Listening...</p>
            )}
        </div>
      </div>
    );
}

const ClientProfileCard: React.FC<ClientProfileCardProps> = ({ profile }) => {
  const fields = [
    { key: 'name', label: 'Client Name', icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" /></svg> },
    { key: 'budget', label: 'Budget', icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v.01" /></svg> },
    { key: 'location', label: 'Location', icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg> },
    { key: 'careLevel', label: 'Care Level', icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg> },
    { key: 'timeline', label: 'Timeline', icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg> },
    { key: 'wheelchairAccessible', label: 'Wheelchair Access', icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M9 2a1 1 0 100 2 1 1 0 000-2z" /><path fillRule="evenodd" d="M9 6.002a.997.997 0 00-1-.998H4.219a1 1 0 100 2H6v3.454a2.5 2.5 0 102 0V6.002zM10.25 15.5a1.25 1.25 0 10-2.5 0 1.25 1.25 0 002.5 0z" clipRule="evenodd" /><path d="M14.75 15.5a1.25 1.25 0 11-2.5 0 1.25 1.25 0 012.5 0zM14 9.412V6.002a.998.998 0 00-1.28-.962l-3.04 1.216a.998.998 0 00-.68.962v2.241a2.502 2.502 0 000 1.085v2.241c0 .416.257.784.631.93l3.089 1.236a1 1 0 001.28-.962V9.412z" /></svg> },
    { key: 'specificDemands', label: 'Specific Demands', icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5 5a3 3 0 015-2.236A3 3 0 0114.83 6H16a2 2 0 110 4h-1.17a3 3 0 01-5.66 0H5a2 2 0 110-4h.17A3 3 0 015 5zm4.242 1.242a.5.5 0 01.708 0l1.25 1.25a.5.5 0 010 .708l-1.25 1.25a.5.5 0 01-.708-.708L9.293 8 8.043 6.75a.5.5 0 010-.708zM6.5 8a.5.5 0 000 1h.5a.5.5 0 000-1h-.5z" clipRule="evenodd" /></svg>},
  ];

  return (
    <div className="bg-white/80 backdrop-blur-md border border-gray-200/80 rounded-xl p-6 h-full shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7 text-blue-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <h2 className="text-xl font-bold text-gray-800">Client Profile</h2>
        </div>
      </div>
       <div className="flex flex-wrap items-center gap-x-3 gap-y-2 mb-6" aria-label="Client profile completion status">
        {fields.map(field => {
            const value = profile[field.key as keyof ClientProfile];
            const isComplete = typeof value === 'boolean' || (typeof value === 'string' && value.length > 0);
            return (
                <div
                    key={field.key}
                    title={`${field.label}: ${isComplete ? 'Complete' : 'Missing'}`}
                    className={`flex items-center text-xs font-semibold px-2.5 py-1 rounded-full transition-all duration-300 ${isComplete ? 'bg-blue-100 text-blue-600' : 'bg-gray-200 text-gray-500'}`}
                >
                    {field.label}
                    {isComplete && (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 ml-1.5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                    )}
                </div>
            )
        })}
       </div>
      <div className="grid grid-cols-1 gap-4">
        {fields.map(field => (
             <ProfileField key={field.key} label={field.label} value={profile[field.key as keyof ClientProfile]} icon={field.icon} />
        ))}
      </div>
    </div>
  );
};

export default ClientProfileCard;
