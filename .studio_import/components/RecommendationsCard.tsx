

import React, { useState, useMemo } from 'react';
import { Recommendation, Community } from '../types';
import MapView from './MapView';

interface RecommendationsCardProps {
  recommendations: Recommendation[];
  allCommunities: Community[];
  onCompare: (communities: Community[]) => void;
}

const PartnerBadge: React.FC = () => (
    <div className="bg-green-100 text-green-700 text-xs font-bold px-2.5 py-1 rounded-full flex items-center gap-1.5">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
        Partner
    </div>
);


const ViewSwitcher: React.FC<{ viewMode: 'list' | 'map'; onViewChange: (mode: 'list' | 'map') => void; }> = ({ viewMode, onViewChange }) => {
    const baseClasses = "p-1.5 rounded-md text-gray-500 hover:text-blue-500 hover:bg-gray-200/80 transition-colors duration-200";
    const activeClasses = "!text-blue-500 bg-blue-100";

    return (
        <div className="flex items-center bg-gray-100/80 rounded-lg p-1 space-x-1">
            <button onClick={() => onViewChange('list')} className={`${baseClasses} ${viewMode === 'list' ? activeClasses : ''}`} aria-label="List View">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
            </button>
            <button onClick={() => onViewChange('map')} className={`${baseClasses} ${viewMode === 'map' ? activeClasses : ''}`} aria-label="Map View">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            </button>
        </div>
    );
};

const RecommendationsCard: React.FC<RecommendationsCardProps> = ({ recommendations, allCommunities, onCompare }) => {
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');

  const communitiesMap = useMemo(() => {
    const map = new Map<string, Community>();
    allCommunities.forEach(c => map.set(c.name, c));
    return map;
  }, [allCommunities]);
  
  const recommendedCommunities = useMemo(() => {
    return recommendations.map(r => communitiesMap.get(r.name)).filter(Boolean) as Community[];
  }, [recommendations, communitiesMap]);


  const handleSelectForComparison = (name: string) => {
    setSelectedForComparison(prev => {
        if(prev.includes(name)) {
            return prev.filter(item => item !== name);
        }
        if(prev.length < 2) {
            return [...prev, name];
        }
        return prev; // Do not allow more than 2 selections
    })
  }
  
  const handleCompareClick = () => {
    const communities = selectedForComparison.map(name => communitiesMap.get(name)).filter(Boolean) as Community[];
    if (communities.length === 2) {
        onCompare(communities);
    }
  }

  const findRecByName = (name: string) => recommendations.find(rec => rec.name === name);

  return (
    <div className="bg-white/80 backdrop-blur-md border border-gray-200/80 rounded-xl p-6 shadow-sm flex flex-col">
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <div className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7 text-blue-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <h2 className="text-xl font-bold text-gray-800">Top Recommendations</h2>
        </div>
        <ViewSwitcher viewMode={viewMode} onViewChange={setViewMode} />
      </div>

       <div className="flex justify-center mb-4 flex-shrink-0">
         <button
            onClick={handleCompareClick}
            disabled={selectedForComparison.length !== 2}
            className="w-full max-w-xs flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed bg-blue-600 border border-transparent text-white hover:bg-blue-700 focus:ring-blue-500"
        >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
               <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a1 1 0 011-1h14a1 1 0 110 2H3a1 1 0 01-1-1z" />
            </svg>
            Compare Selected ({selectedForComparison.length})
        </button>
      </div>

      <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-2">
        {recommendations.length > 0 ? (
            viewMode === 'list' ? (
                recommendedCommunities.map((community, index) => {
                  const rec = findRecByName(community.name);
                  if (!rec) return null;

                  const isSelected = selectedForComparison.includes(rec.name);
                  const isPartner = community.isPartner;
                  const availability = community.availability;
                  
                  let availabilityColor = 'bg-gray-100 text-gray-700';
                  if(availability === 'Immediate') availabilityColor = 'bg-green-100 text-green-700';
                  if(availability === 'Waitlist') availabilityColor = 'bg-red-100 text-red-700';
                  if(availability === 'Available Soon') availabilityColor = 'bg-yellow-100 text-yellow-700';

                  return (
                    <div key={index} className={`border p-4 rounded-lg transition-all duration-300 relative ${isPartner ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'} ${isSelected ? 'shadow-lg ring-2 ring-offset-2 ring-offset-white ring-blue-500 border-blue-500' : 'hover:border-gray-300 hover:shadow-md'}`}>
                      <div className="flex justify-between items-start">
                          <h3 className="font-bold text-gray-800 text-lg flex items-center pr-24">
                            <input 
                                  type="checkbox"
                                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3 cursor-pointer"
                                  checked={isSelected}
                                  onChange={() => handleSelectForComparison(rec.name)}
                                  disabled={!isSelected && selectedForComparison.length >= 2}
                              />
                              {rec.name}
                          </h3>
                          {isPartner && <div className="absolute top-4 right-4"><PartnerBadge /></div>}
                      </div>
                      
                      <p className="text-gray-500 mt-1 text-sm ml-7">{rec.reason}</p>

                      <div className="mt-4 pt-3 border-t border-gray-200/80 text-sm space-y-2 ml-7">
                        <div className="flex items-center">
                          <span className="font-semibold w-28 text-gray-500">Availability:</span>
                          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${availabilityColor}`}>{availability}</span>
                        </div>
                        {rec.price && (
                          <p className="text-gray-700 flex items-center">
                              <span className="font-semibold w-28 text-gray-500">Price:</span>
                              <span>{rec.price}</span>
                          </p>
                        )}
                        {rec.careLevels && rec.careLevels.length > 0 && (
                          <p className="text-gray-700 flex items-center">
                              <span className="font-semibold w-28 text-gray-500">Care Levels:</span>
                              <span className="flex flex-wrap gap-1">
                                  {rec.careLevels.map(level => <span key={level} className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">{level}</span>)}
                              </span>
                          </p>
                        )}
                      </div>
                    </div>
                  )
                })
            ) : (
                <div className="h-[400px] w-full bg-gray-200 rounded-lg">
                    <MapView communities={recommendedCommunities} />
                </div>
            )
        ) : (
          <div className="text-center py-12 bg-gray-50/80 rounded-lg border-2 border-dashed border-gray-200">
            <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <p className="mt-2 text-gray-600 font-semibold">Awaiting Recommendations</p>
            <p className="mt-1 text-gray-500 text-sm">Start a call to get AI-powered suggestions.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default RecommendationsCard;
