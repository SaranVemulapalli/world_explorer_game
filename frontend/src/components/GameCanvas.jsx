import React, { useEffect, useRef } from 'react';
import Phaser from 'phaser';

// Define the size of your tiles (MUST match your actual tile image size, e.g., 32 for 32x32px tiles)
const TILE_SIZE = 32;

const GameCanvas = () => {
    const gameContainerRef = useRef(null); // Ref for the DOM element where Phaser will render

    useEffect(() => {
        // Phaser game configuration
        const config = {
            type: Phaser.AUTO, // Use WebGL if available, otherwise Canvas
            width: window.innerWidth, // Full browser window width
            height: window.innerHeight, // Full browser window height
            parent: gameContainerRef.current, // Attach Phaser game to this div
            physics: {
                default: 'arcade', // Simple Arcade physics for player movement
                arcade: {
                    debug: false // Set to true to see hitboxes for debugging
                }
            },
            scene: {
                // Define the three core Phaser scene methods
                preload: preload,
                create: create,
                update: update
            }
        };

        const game = new Phaser.Game(config); // Create the Phaser game instance

        // Variables to be used across Phaser scene methods (declared globally within the scope of useEffect)
        let player;
        let cursors;
        let map;
        let tileset;
        let worldLayer; // The layer where our tiles will be rendered

        // --- Phaser Scene Methods ---

        // 1. preload(): Load assets before the game starts
        function preload () {
            // Load your tile images (make sure they are in public/assets)
            // 'tiles' is the key you'll use to refer to this image in Phaser
            // 'assets/tilesheet.png' is the path relative to your `public` folder
            this.load.image('tiles', 'assets/tilesheet.png');
            this.load.image('player', 'assets/player.png'); // Simple player sprite
            console.log("Phaser: preload completed. Assets requested.");
        }

        // 2. create(): Initialize game objects once assets are loaded
        async function create () {
            console.log("Phaser: create function started.");

            // Fetch world data from your Flask backend
            try {
                const response = await fetch('http://127.0.0.1:5000/generate_world?seed=123&size=64');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const worldData = await response.json();
                const { size, tiles } = worldData;

                // --- DEBUGGING CONSOLE LOGS ---
                console.log("World data received:", worldData);
                console.log("Map size (from worldData):", size);
                console.log("Tiles array (from worldData):", tiles); // Check if tiles is a valid array

                if (!Array.isArray(tiles) || tiles.length === 0 || !Array.isArray(tiles[0])) {
                    console.error("Error: 'tiles' data from backend is not a valid 2D array.", tiles);
                    // Prevent further execution if tiles data is bad
                    return;
                }

                map = this.make.tilemap({ data: tiles, tileWidth: TILE_SIZE, tileHeight: TILE_SIZE });

                // --- DEBUGGING CONSOLE LOGS ---
                console.log("Map object created:", map); // Check if map is a valid Phaser.Tilemap object
                if (map) {
                    console.log("Map width in pixels:", map.widthInPixels); // Check map dimensions
                    console.log("Map height in pixels:", map.heightInPixels);
                } else {
                    console.error("Error: Phaser.Tilemap object 'map' was not created successfully.");
                    return; // Stop if map is not valid
                }


                tileset = map.addTilesetImage('tiles', 'tiles', TILE_SIZE, TILE_SIZE, 0, 0);
                console.log("Tileset added:", tileset);


                worldLayer = map.createLayer(0, tileset, 0, 0);
                console.log("World layer created:", worldLayer);


                this.physics.world.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
                console.log("Physics world bounds set.");

                // Add player character
                player = this.physics.add.sprite(map.widthInPixels / 2, map.heightInPixels / 2, 'player');

                // --- DEBUGGING CONSOLE LOGS ---
                console.log("Player sprite created:", player); // Check if player is a valid Phaser.GameObjects.Sprite object
                if (player) {
                    player.setCollideWorldBounds(true);
                    console.log("Player collide world bounds set.");
                } else {
                    console.error("Error: Player sprite was not created successfully. Check 'player' asset key or if map dimensions are valid.");
                    return; // Stop if player is not valid
                }


                // Configure camera to follow player
                this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
                this.cameras.main.startFollow(player, true, 0.05, 0.05); // Follow with a slight lerp (smoothness)
                this.cameras.main.setZoom(1); // Adjust zoom level (1 means no zoom)
                console.log("Camera configured to follow player.");

                // Input setup: create cursor keys for movement
                cursors = this.input.keyboard.createCursorKeys();
                console.log("Cursor keys input created.");

            } catch (error) {
                console.error("Error during Phaser create function or fetching world data:", error);
            }
            console.log("Phaser: create function finished.");
        }

        // 3. update(): Game loop, runs every frame
        function update () {
            // Only attempt to update player if it exists
            if (player) {
                player.setVelocity(0);

                // Handle player movement based on cursor keys
                // The player speed (160) can be adjusted
                if (cursors.left.isDown) {
                    player.setVelocityX(-160); // Move left
                } else if (cursors.right.isDown) {
                    player.setVelocityX(160); // Move right
                }

                if (cursors.up.isDown) {
                    player.setVelocityY(-160); // Move up
                } else if (cursors.down.isDown) {
                    player.setVelocityY(160); // Move down
                }

                // Normalize diagonal speed (optional but good practice)
                // If moving diagonally (e.g., both up and left), the combined velocity would be sqrt(vx^2 + vy^2)
                // which is faster than horizontal/vertical. Normalizing keeps diagonal speed consistent.
                player.body.velocity.normalize().scale(160);
            } else {
                // console.warn("Player sprite is not defined in update function. Waiting for creation...");
            }
        }

        // Cleanup function for React's useEffect
        // This ensures the Phaser game instance is properly destroyed when the React component unmounts
        return () => {
            console.log("Phaser: Game instance being destroyed.");
            game.destroy(true);
        };
    }, []); // Empty dependency array ensures useEffect runs only once on component mount

    // Render the div where Phaser will inject its canvas
    return <div ref={gameContainerRef} style={{ width: '100vw', height: '100vh', overflow: 'hidden' }} />;
};

export default GameCanvas;