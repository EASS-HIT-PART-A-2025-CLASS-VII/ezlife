// SettingsPage.jsx - User Settings Page
import React, { useState } from 'react';
import axios from 'axios';

function SettingsPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSave = async () => {
    try {
      await axios.put('/settings', { email, password });
      alert('Settings updated');
    } catch (error) {
      alert('Update failed');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <div className="bg-white p-8 rounded shadow-md w-96">
        <h2 className="text-2xl font-bold mb-6 text-center">User Settings</h2>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" className="w-full mb-4 p-2 border border-gray-300 rounded" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" className="w-full mb-6 p-2 border border-gray-300 rounded" />
        <button onClick={handleSave} className="w-full bg-yellow-500 text-white py-2 rounded hover:bg-yellow-600">Save Changes</button>
      </div>
    </div>
  );
}

export default SettingsPage;
