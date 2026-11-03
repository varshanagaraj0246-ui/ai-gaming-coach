if (event.key === 'ArrowLeft') {
        setPlayerX((x) => Math.max(0, x - 10))
      }

      if (event.key === 'ArrowRight') {
        setPlayerX((x) => Math.min(760, x + 10))
      }

      if(event.key === 'ArrowUp'){
        setPlayerY((y) => Math.max(0, y - 10))
      }

      if(event.key === 'ArrowDown'){
        setPlayerY((y) => Math.min(560, y + 10))
      }

      if(event.code === 'Space'){
        const newBullet = {
          x: playerX + 18,
          y: playerY - 15,
        }

        console.log("bulet created", newBullet)
        setBullets((oldBullets) => [...oldBullets, newBullet])
      }


      