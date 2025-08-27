import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Mood options matching backend
const MOODS = {
  1: { emoji: "😢", label: "Very Sad" },
  2: { emoji: "😕", label: "Sad" },
  3: { emoji: "😐", label: "Neutral" },
  4: { emoji: "🙂", label: "Happy" },
  5: { emoji: "😄", label: "Very Happy" }
};

function App() {
  const [currentView, setCurrentView] = useState('entry');
  const [moods, setMoods] = useState([]);
  const [selectedMood, setSelectedMood] = useState(null);
  const [notes, setNotes] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [stats, setStats] = useState(null);
  const [editingEntry, setEditingEntry] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  const fetchMoods = async () => {
    try {
      const response = await axios.get(`${API}/moods`);
      setMoods(response.data);
    } catch (error) {
      console.error('Error fetching moods:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/moods/stats/summary`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  useEffect(() => {
    fetchMoods();
    fetchStats();
  }, []);

  const submitMoodEntry = async () => {
    if (!selectedMood) {
      setMessage('Please select a mood!');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/moods`, {
        entry_date: selectedDate,
        mood_score: selectedMood,
        notes: notes.trim() || null
      });
      
      setMessage('Mood saved successfully! 🎉');
      setSelectedMood(null);
      setNotes('');
      fetchMoods();
      fetchStats();
      
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      if (error.response?.status === 400) {
        setMessage('You already have a mood entry for this date!');
      } else {
        setMessage('Error saving mood. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const exportData = async () => {
    try {
      const response = await axios.get(`${API}/moods/export/csv`);
      const blob = new Blob([response.data.csv_data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mood-tracker-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setMessage('Data exported successfully! 📊');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Error exporting data. Please try again.');
    }
  };

  const getMoodForDate = (date) => {
    return moods.find(mood => mood.entry_date === date);
  };

  const generateCalendarDays = () => {
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    const firstDay = new Date(currentYear, currentMonth, 1);
    const lastDay = new Date(currentYear, currentMonth + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const calendarDays = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      calendarDays.push(null);
    }
    
    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      calendarDays.push({
        day,
        date: dateStr,
        mood: getMoodForDate(dateStr)
      });
    }
    
    return calendarDays;
  };

  const renderMoodEntry = () => (
    <div className="max-w-md mx-auto bg-white rounded-2xl shadow-xl p-8">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">How are you feeling today?</h2>
      
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          max={new Date().toISOString().split('T')[0]}
        />
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-4">Select your mood</label>
        <div className="grid grid-cols-5 gap-3">
          {Object.entries(MOODS).map(([score, mood]) => (
            <button
              key={score}
              onClick={() => setSelectedMood(parseInt(score))}
              className={`p-4 rounded-xl transition-all duration-200 border-2 ${
                selectedMood === parseInt(score)
                  ? 'border-blue-500 bg-blue-50 scale-110'
                  : 'border-gray-200 hover:border-gray-300 hover:scale-105'
              }`}
            >
              <div className="text-3xl mb-1">{mood.emoji}</div>
              <div className="text-xs text-gray-600 font-medium">{mood.label}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Notes (optional)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="What's on your mind today?"
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          rows="3"
          maxLength="200"
        />
        <div className="text-right text-xs text-gray-500 mt-1">{notes.length}/200</div>
      </div>

      <button
        onClick={submitMoodEntry}
        disabled={loading || !selectedMood}
        className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
      >
        {loading ? 'Saving...' : 'Save Mood 💾'}
      </button>
    </div>
  );

  const renderCalendarView = () => {
    const calendarDays = generateCalendarDays();
    const monthNames = ["January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"];
    const today = new Date();
    
    return (
      <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">
          {monthNames[today.getMonth()]} {today.getFullYear()} Calendar
        </h2>
        
        <div className="grid grid-cols-7 gap-2 mb-4">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className="text-center font-semibold text-gray-600 py-2">
              {day}
            </div>
          ))}
        </div>
        
        <div className="grid grid-cols-7 gap-2">
          {calendarDays.map((dayData, index) => (
            <div
              key={index}
              className="aspect-square border border-gray-200 rounded-lg p-2 relative hover:bg-gray-50"
            >
              {dayData && (
                <>
                  <div className="text-sm font-medium text-gray-700">{dayData.day}</div>
                  {dayData.mood && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-2xl" title={dayData.mood.notes || 'No notes'}>
                        {dayData.mood.emoji}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
        
        <div className="mt-6 text-center">
          <div className="text-sm text-gray-600">
            Hover over emojis to see notes • Missing days have no mood entries
          </div>
        </div>
      </div>
    );
  };

  const renderHistoryView = () => (
    <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-gray-800">Mood History</h2>
        <button
          onClick={exportData}
          className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
        >
          Export CSV 📊
        </button>
      </div>
      
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6 rounded-xl text-center">
            <div className="text-3xl font-bold">{stats.total_entries}</div>
            <div className="text-sm opacity-90">Total Entries</div>
          </div>
          <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-6 rounded-xl text-center">
            <div className="text-3xl font-bold">{stats.average_mood}</div>
            <div className="text-sm opacity-90">Average Mood</div>
          </div>
          <div className="bg-gradient-to-r from-orange-500 to-red-600 text-white p-6 rounded-xl text-center">
            <div className="text-3xl font-bold">{Object.keys(stats.mood_distribution).length}</div>
            <div className="text-sm opacity-90">Mood Types Used</div>
          </div>
        </div>
      )}

      <div className="space-y-4 max-h-96 overflow-y-auto">
        {moods.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No mood entries yet. Start by adding your first mood! 😊
          </div>
        ) : (
          moods.map((mood) => (
            <div key={mood.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">{mood.emoji}</span>
                  <div>
                    <div className="font-semibold text-gray-800">
                      {MOODS[mood.mood_score].label}
                    </div>
                    <div className="text-sm text-gray-600">{mood.entry_date}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-700">Score: {mood.mood_score}/5</div>
                </div>
              </div>
              {mood.notes && (
                <div className="mt-2 p-3 bg-gray-50 rounded text-sm text-gray-700">
                  <strong>Notes:</strong> {mood.notes}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-800 flex items-center">
              🌈 Mood Tracker
            </h1>
            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentView('entry')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'entry'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-600 hover:text-blue-500'
                }`}
              >
                Add Mood
              </button>
              <button
                onClick={() => setCurrentView('calendar')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'calendar'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-600 hover:text-blue-500'
                }`}
              >
                Calendar
              </button>
              <button
                onClick={() => setCurrentView('history')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'history'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-600 hover:text-blue-500'
                }`}
              >
                History
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {message && (
          <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg text-center">
            {message}
          </div>
        )}

        {currentView === 'entry' && renderMoodEntry()}
        {currentView === 'calendar' && renderCalendarView()}
        {currentView === 'history' && renderHistoryView()}
      </main>

      {/* Footer */}
      <footer className="mt-16 bg-gray-50 border-t">
        <div className="max-w-6xl mx-auto px-4 py-6 text-center text-gray-600">
          <p>Track your daily moods and build emotional awareness 🧠💙</p>
        </div>
      </footer>
    </div>
  );
}

export default App;