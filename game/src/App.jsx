import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const dataSentRef = useRef(false)

  const [playerX, setPlayerX] = useState(375)
  const [playerY, setPlayerY] = useState(275)

  const [bullets, setBullets] = useState([])

  const [enemies, setEnemies] = useState([
    { x: 100, y: 50, speed: 2 },
    { x: 380, y: 100, speed: 3 },
    { x: 650, y: 50, speed: 4 }
  ])

  const [score, setScore] = useState(0)
  const [health, setHealth] = useState(3)
  const [time, setTime] = useState(60)

  const [difficulty, setDifficulty] = useState('Medium')

  const [bulletsFired, setBulletsFired] = useState(0)
  const [enemiesDefeated, setEnemiesDefeated] = useState(0)
  const [playerHits, setPlayerHits] = useState(0)

  const [gameStarted, setGameStarted] = useState(false)

  const [explosions, setExplosions] = useState([])

  const gameOver =
    gameStarted && (health === 0 || time === 0)

  const difficultySpeeds = {
    Easy: [1, 1.5, 2],
    Medium: [2, 3, 4],
    Hard: [3, 4, 5]
  }

  const changeDifficulty = (level) => {
    setDifficulty(level)

    const speeds = difficultySpeeds[level]

    setEnemies((oldEnemies) =>
      oldEnemies.map((enemy, index) => ({
        ...enemy,
        speed: speeds[index]
      }))
    )
  }

  const startGame = () => {
    // Allow the new game to send its data once
    dataSentRef.current = false

    const speeds = difficultySpeeds[difficulty]

    setPlayerX(375)
    setPlayerY(275)

    setBullets([])

    setEnemies([
      { x: 100, y: 50, speed: speeds[0] },
      { x: 380, y: 100, speed: speeds[1] },
      { x: 650, y: 50, speed: speeds[2] }
    ])

    setScore(0)
    setHealth(3)
    setTime(60)

    setBulletsFired(0)
    setEnemiesDefeated(0)
    setPlayerHits(0)

    setExplosions([])

    setGameStarted(true)
  }

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (!gameStarted || gameOver) return

      if (
        ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(
          event.key
        )
      ) {
        event.preventDefault()
      }

      if (event.key === 'ArrowLeft') {
        setPlayerX((x) => Math.max(0, x - 10))
      }

      if (event.key === 'ArrowRight') {
        setPlayerX((x) => Math.min(760, x + 10))
      }

      if (event.key === 'ArrowUp') {
        setPlayerY((y) => Math.max(0, y - 10))
      }

      if (event.key === 'ArrowDown') {
        setPlayerY((y) => Math.min(560, y + 10))
      }

      if (event.code === 'Space') {
        const newBullet = {
          x: playerX + 17,
          y: playerY - 15
        }

        setBullets((oldBullets) => [
          ...oldBullets,
          newBullet
        ])

        setBulletsFired((oldCount) => oldCount + 1)
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [playerX, playerY, gameStarted, gameOver])

  useEffect(() => {
    const bulletTimer = setInterval(() => {
      if (!gameStarted || gameOver) return

      setBullets((oldBullets) => {
        const newBullets = []

        oldBullets.forEach((bullet) => {
          const hitEnemyIndex = enemies.findIndex((enemy) =>
            isColliding(bullet, enemy)
          )

          if (hitEnemyIndex !== -1) {
            const hitEnemy = enemies[hitEnemyIndex]

            setScore((oldScore) => oldScore + 1)

            setEnemiesDefeated((oldCount) => oldCount + 1)

            setExplosions((oldExplosions) => [
              ...oldExplosions,
              {
                id: Date.now() + Math.random(),
                x: hitEnemy.x,
                y: hitEnemy.y
              }
            ])

            setTimeout(() => {
              setExplosions((oldExplosions) =>
                oldExplosions.slice(1)
              )
            }, 350)

            setEnemies((oldEnemies) =>
              oldEnemies.map((enemy, index) => {
                if (index === hitEnemyIndex) {
                  return {
                    ...enemy,
                    x: Math.floor(Math.random() * 760),
                    y: 50
                  }
                }

                return enemy
              })
            )
          } else if (bullet.y > -15) {
            newBullets.push({
              ...bullet,
              y: bullet.y - 10
            })
          }
        })

        return newBullets
      })
    }, 30)

    return () => {
      clearInterval(bulletTimer)
    }
  }, [enemies, gameStarted, gameOver])

  useEffect(() => {
    const enemyTimer = setInterval(() => {
      if (!gameStarted || gameOver) return

      setEnemies((oldEnemies) =>
        oldEnemies.map((enemy) => {
          if (enemy.y >= 500) {
            return {
              ...enemy,
              y: 50
            }
          }

          return {
            ...enemy,
            y: enemy.y + enemy.speed
          }
        })
      )
    }, 100)

    return () => {
      clearInterval(enemyTimer)
    }
  }, [gameStarted, gameOver])

  useEffect(() => {
    const collisionTimer = setInterval(() => {
      if (!gameStarted || gameOver) return

      setEnemies((oldEnemies) =>
        oldEnemies.map((enemy) => {
          if (isPlayerHit(playerX, playerY, enemy)) {
            setHealth((oldHealth) =>
              Math.max(0, oldHealth - 1)
            )

            setPlayerHits((oldCount) => oldCount + 1)

            return {
              ...enemy,
              y: 50,
              x: Math.floor(Math.random() * 760)
            }
          }

          return enemy
        })
      )
    }, 500)

    return () => {
      clearInterval(collisionTimer)
    }
  }, [playerX, playerY, gameStarted, gameOver])

  useEffect(() => {
    const timer = setInterval(() => {
      if (!gameStarted || gameOver) return

      setTime((oldTime) => {
        if (oldTime <= 0) {
          return 0
        }

        return oldTime - 1
      })
    }, 1000)

    return () => {
      clearInterval(timer)
    }
  }, [gameStarted, gameOver])

  // SEND COMPLETED GAME DATA TO FLASK
  useEffect(() => {
    if (!gameOver || dataSentRef.current) {
      return
    }

    // Prevent duplicate submissions
    dataSentRef.current = true

    const accuracy =
      bulletsFired > 0
        ? Math.round((enemiesDefeated / bulletsFired) * 100)
        : 0

    const gameData = {
      score: score,
      accuracy: accuracy,
      kills: enemiesDefeated,
      deaths: playerHits,
      reaction_time: 0,
      survival_time: 60 - time,
      damage_received: playerHits,
      difficulty: difficulty,
      skill_level:
        enemiesDefeated >= 10
          ? 'Advanced'
          : enemiesDefeated >= 5
          ? 'Intermediate'
          : 'Beginner'
    }

    console.log('🎮 GAME DATA BEING SENT TO BACKEND')
    console.table(gameData)

    fetch('http://127.0.0.1:5000/api/session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(gameData)
    })
      .then(async (response) => {
        const data = await response.json()

        if (!response.ok) {
          throw new Error(
            data.error || 'Server returned an error'
          )
        }

        return data
      })
      .then((data) => {
        console.log('✅ GAME DATA SAVED SUCCESSFULLY')
        console.log(data)
      })
      .catch((error) => {
        console.error('❌ FAILED TO SEND GAME DATA')
        console.error(error)

        // Allow another attempt if the server was unavailable
        dataSentRef.current = false
      })
  }, [
    gameOver,
    score,
    bulletsFired,
    enemiesDefeated,
    playerHits,
    time,
    difficulty
  ])

  const isColliding = (bullet, enemy) => {
    return (
      bullet.x < enemy.x + 40 &&
      bullet.x + 5 > enemy.x &&
      bullet.y < enemy.y + 40 &&
      bullet.y + 15 > enemy.y
    )
  }

  const isPlayerHit = (playerX, playerY, enemy) => {
    return (
      playerX < enemy.x + 40 &&
      playerX + 40 > enemy.x &&
      playerY < enemy.y + 40 &&
      playerY + 40 > enemy.y
    )
  }

  const restartGame = () => {
    startGame()
  }

  const accuracy =
    bulletsFired > 0
      ? Math.round((enemiesDefeated / bulletsFired) * 100)
      : 0

  if (!gameStarted) {
    return (
      <div className="game-screen start-screen">
        <div className="ambient-orb orb-one"></div>
        <div className="ambient-orb orb-two"></div>

        <div className="start-content">
          <div className="title-chip">
            <span className="live-dot"></span>
            AI POWERED COMBAT TRAINING
          </div>

          <h1 className="main-title">
            <span>AI</span> GAMING COACH
          </h1>

          <div className="title-line">
            <span></span>
            <p>ENTER THE TRAINING ARENA</p>
            <span></span>
          </div>

          <p className="start-description">
            Improve your aim. Survive the arena. Defeat the enemies.
          </p>

          <div className="difficulty-panel">
            <div className="difficulty-label">
              SELECT TRAINING LEVEL
            </div>

            <div className="difficulty-buttons">
              <button
                className={difficulty === 'Easy' ? 'active easy' : 'easy'}
                onClick={() => changeDifficulty('Easy')}
              >
                <span>●</span>
                EASY
              </button>

              <button
                className={
                  difficulty === 'Medium'
                    ? 'active medium'
                    : 'medium'
                }
                onClick={() => changeDifficulty('Medium')}
              >
                <span>●</span>
                MEDIUM
              </button>

              <button
                className={difficulty === 'Hard' ? 'active hard' : 'hard'}
                onClick={() => changeDifficulty('Hard')}
              >
                <span>●</span>
                HARD
              </button>
            </div>
          </div>

          <button className="start-button" onClick={startGame}>
            <span>▶</span>
            START GAME
          </button>

          <div className="mission-briefing">
  <div className="mission-header">
    <span className="mission-status-dot"></span>
    <h2>MISSION BRIEFING</h2>
    <span className="mission-tag">OPERATION: SURVIVAL</span>
  </div>

  <div className="mission-instruction">
    <span className="mission-number">01</span>
    <span className="mission-action">MOVE</span>
    <span className="mission-detail">
      Navigate using arrow keys
    </span>
    <kbd>↑ ↓ ← →</kbd>
  </div>

  <div className="mission-instruction">
    <span className="mission-number">02</span>
    <span className="mission-action">ATTACK</span>
    <span className="mission-detail">
      Fire at enemy targets
    </span>
    <kbd>SPACE</kbd>
  </div>

  <div className="mission-instruction">
    <span className="mission-number">03</span>
    <span className="mission-action">SURVIVE</span>
    <span className="mission-detail">
      Protect your health and defeat enemies
    </span>
    <span className="mission-objective">OBJECTIVE</span>
  </div>
</div>
        </div>
      </div>
    )
  }

  return (
    <div
      className={`game-screen ${
        health === 1 ? 'danger-mode' : ''
      }`}
    >
      <div className="ambient-orb orb-one"></div>
      <div className="ambient-orb orb-two"></div>

      <header className="game-header">
        <div className="brand-area">
          <div className="brand-icon">⚡</div>

          <div>
            <div className="brand-title">
              AI GAMING COACH
            </div>

            <div className="brand-subtitle">
              COMBAT TRAINING ARENA
            </div>
          </div>
        </div>

        <div className="live-status">
          <span className="live-dot"></span>
          LIVE SESSION
        </div>
      </header>

      <div className="hud">
        <div className="hud-stat score-stat">
          <span className="hud-label">SCORE</span>
          <strong>{score}</strong>
        </div>

        <div className="hud-stat kill-stat">
          <span className="hud-label">KILLS</span>
          <strong>{enemiesDefeated}</strong>
        </div>

        <div className="hud-stat health-stat">
          <span className="hud-label">HEALTH</span>
          <strong>
            {'♥'.repeat(health)}
            <span className="empty-hearts">
              {'♥'.repeat(3 - health)}
            </span>
          </strong>
        </div>

        <div className="hud-stat time-stat">
          <span className="hud-label">TIME</span>
          <strong>{time}s</strong>
        </div>
      </div>

      <div className="difficulty">
        <div className="difficulty-title">
          TRAINING LEVEL
          <span>{difficulty}</span>
        </div>

        <div className="difficulty-buttons">
          <button
            className={difficulty === 'Easy' ? 'active easy' : 'easy'}
            onClick={() => changeDifficulty('Easy')}
          >
            <span>●</span>
            Easy
          </button>

          <button
            className={
              difficulty === 'Medium'
                ? 'active medium'
                : 'medium'
            }
            onClick={() => changeDifficulty('Medium')}
          >
            <span>●</span>
            Medium
          </button>

          <button
            className={difficulty === 'Hard' ? 'active hard' : 'hard'}
            onClick={() => changeDifficulty('Hard')}
          >
            <span>●</span>
            Hard
          </button>
        </div>
      </div>

      <div className="arena-wrapper">
        <div className="arena-top-line">
          <span>TRAINING ZONE</span>
          <span>
            THREAT LEVEL: {health === 1 ? 'HIGH' : 'ACTIVE'}
          </span>
        </div>

        <div className="game-board">
          <div className="arena-scan"></div>

          <div className="arena-corner corner-tl"></div>
          <div className="arena-corner corner-tr"></div>
          <div className="arena-corner corner-bl"></div>
          <div className="arena-corner corner-br"></div>

          <div className="arena-center-ring"></div>

          <div
            className="player"
            style={{
              left: `${playerX}px`,
              top: `${playerY}px`
            }}
          >
            <div className="player-core"></div>
            <div className="player-ring"></div>
            <div className="player-direction"></div>
          </div>

          {bullets.map((bullet, index) => (
            <div
              key={index}
              className="bullet"
              style={{
                left: `${bullet.x}px`,
                top: `${bullet.y}px`
              }}
            >
              <div className="bullet-core"></div>
            </div>
          ))}

          {enemies.map((enemy, index) => (
            <div
              key={index}
              className={`enemy enemy-${index + 1}`}
              style={{
                left: `${enemy.x}px`,
                top: `${enemy.y}px`
              }}
            >
              <div className="enemy-core"></div>
              <div className="enemy-eye"></div>
            </div>
          ))}

          {explosions.map((explosion) => (
            <div
              key={explosion.id}
              className="explosion"
              style={{
                left: `${explosion.x}px`,
                top: `${explosion.y}px`
              }}
            >
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>
          ))}

          {gameOver && (
            <div className="game-over-overlay">
              <div className="game-over-card">
                <div className="game-over-icon">
                  {health === 0 ? '☠' : '⌛'}
                </div>

                <div className="game-over-tag">
                  {health === 0
                    ? 'MISSION FAILED'
                    : 'TIME COMPLETE'}
                </div>

                <h2>GAME OVER</h2>

                <p className="result-text">
                  {health === 0
                    ? 'Your health reached zero.'
                    : 'Training session completed.'}
                </p>

                <div className="final-stats">
                  <div>
                    <span>SCORE</span>
                    <strong>{score}</strong>
                  </div>

                  <div>
                    <span>KILLS</span>
                    <strong>{enemiesDefeated}</strong>
                  </div>

                  <div>
                    <span>ACCURACY</span>
                    <strong>{accuracy}%</strong>
                  </div>
                </div>

                <button
                  className="restart-button"
                  onClick={restartGame}
                >
                  ↻ PLAY AGAIN
                </button>

                {/* NEW: HOME AND DASHBOARD NAVIGATION */}
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '12px',
                    marginTop: '16px'
                  }}
                >
                  <a
                    href="/"
                    style={{
                      display: 'inline-flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      padding: '12px 16px',
                      color: '#20eaff',
                      background: 'rgba(0, 170, 255, 0.1)',
                      border: '1px solid #20eaff',
                      borderRadius: '8px',
                      textDecoration: 'none',
                      fontSize: '12px',
                      fontWeight: '800',
                      letterSpacing: '0.5px',
                      cursor: 'pointer',
                      transition: 'all 0.25s ease'
                    }}
                  >
                    🏠 BACK TO HOME
                  </a>

                  <a
                    href="/dashboard.html"
                    style={{
                      display: 'inline-flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      padding: '12px 16px',
                      color: '#ffffff',
                      background: 'linear-gradient(135deg, #1677ff, #9b5cff)',
                      border: '1px solid #1677ff',
                      borderRadius: '8px',
                      textDecoration: 'none',
                      fontSize: '12px',
                      fontWeight: '800',
                      letterSpacing: '0.5px',
                      cursor: 'pointer',
                      transition: 'all 0.25s ease'
                    }}
                  >
                    📊 VIEW DASHBOARD
                  </a>
                </div>
                {/* END OF NEW NAVIGATION BUTTONS */}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="bottom-panel">
        <div className="mission-info">
          <span className="mission-icon">⚡</span>

          <div>
            <strong>MISSION</strong>
            <span>Eliminate incoming targets</span>
          </div>
        </div>

        <div className="control-info">
          <span>
            <b>← ↑ ↓ →</b> MOVE
          </span>

          <span>
            <b>SPACE</b> SHOOT
          </span>
        </div>

        <div className="session-info">
          <span>FIRED</span>
          <strong>{bulletsFired}</strong>

          <span>HITS TAKEN</span>
          <strong>{playerHits}</strong>
        </div>
      </div>

      <p className="instructions">
        Stay alert • Track the targets • Improve your performance
      </p>
    </div>
  )
}

export default App