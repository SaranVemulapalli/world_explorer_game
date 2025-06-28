import React from 'react';
import GameCanvas from './components/GameCanvas'; // Path to your game component
import './App.css'; // Keep this for basic styling or remove if not needed

function App() {
  return (
    <div className="App">
      {/* The GameCanvas component will render your Phaser game */}
      <GameCanvas />
    </div>
  );
}

export default App;
