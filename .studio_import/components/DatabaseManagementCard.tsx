
import React, { useState, useMemo } from 'react';
import { Community } from '../types';

interface DatabaseManagementCardProps {
    communities: Community[];
    onAdd: () => void;
    onEdit: (community: Community) => void;
    onDelete: (communityId: number) => void;
}

const StatCard: React.FC<{label: string, value: string | number, icon: React.ReactNode}> = ({label, value, icon}) => (
    <div className="bg-white/80 backdrop-blur-md border border-gray-200/80 rounded-xl p-4 flex items-center gap-4 shadow-sm">
        <div className="flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center bg-blue-100 text-blue-500">
            {icon}
        </div>
        <div>
            <div className="text-sm text-gray-500">{label}</div>
            <div className="text-2xl font-bold text-gray-800">{value}</div>
        </div>
    </div>
);


const DatabaseManagementCard: React.FC<DatabaseManagementCardProps> = ({ communities, onAdd, onEdit, onDelete }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const stats = useMemo(() => {
        const total = communities.length;
        const avgPrice = total > 0 ? communities.reduce((sum, c) => sum + c.basePrice, 0) / total : 0;
        const partners = communities.filter(c => c.isPartner).length;
        return {
            total,
            avgPrice: `$${avgPrice.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
            partners
        };
    }, [communities]);

    const filteredCommunities = useMemo(() => {
        if (!searchTerm) return communities;
        const lowercasedTerm = searchTerm.toLowerCase();
        return communities.filter(c =>
            c.name.toLowerCase().includes(lowercasedTerm) ||
            c.location.toLowerCase().includes(lowercasedTerm) ||
            c.address.toLowerCase().includes(lowercasedTerm) ||
            c.careLevels.some(level => level.toLowerCase().includes(lowercasedTerm)) ||
            c.id.toString().includes(lowercasedTerm)
        );
    }, [communities, searchTerm]);

    return (
        <div className="bg-white/80 backdrop-blur-md border border-gray-200/80 rounded-xl p-6 shadow-sm w-full h-full flex flex-col">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Community Database Management</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <StatCard label="Total Communities" value={stats.total} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m-1 4h1m5-4h1m-1 4h1m-1-4h1m-1 4h1" /></svg>} />
                <StatCard label="Average Base Price" value={stats.avgPrice} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v.01" /></svg>} />
                <StatCard label="Partner Communities" value={stats.partners} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>} />
            </div>

            <div className="flex items-center justify-between mb-4">
                <div className="relative w-full max-w-sm">
                    <input 
                        type="text" 
                        placeholder="Search communities..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                </div>
                <button
                    onClick={onAdd}
                    className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all duration-200 bg-blue-600 border border-transparent text-white hover:bg-blue-700 focus:ring-blue-500"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" /></svg>
                    Add New Community
                </button>
            </div>
            
            <div className="flex-grow overflow-y-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 sticky top-0">
                        <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Base Price</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Care Levels</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Availability</th>
                            <th scope="col" className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {filteredCommunities.map(community => (
                            <tr key={community.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm font-semibold text-gray-900">{community.name}</div>
                                    <div className="text-xs text-gray-500">ID: {community.id}</div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{community.location}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${community.basePrice.toLocaleString()}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex flex-wrap gap-1">
                                        {community.careLevels.map(level => <span key={level} className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">{level}</span>)}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                        community.availability === 'Immediate' ? 'bg-green-100 text-green-800' :
                                        community.availability === 'Waitlist' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                        {community.availability}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button onClick={() => onEdit(community)} className="text-blue-600 hover:text-blue-900 mr-4">Edit</button>
                                    <button onClick={() => onDelete(community.id)} className="text-red-600 hover:text-red-900">Delete</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default DatabaseManagementCard;
