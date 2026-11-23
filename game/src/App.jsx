
import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const dataSentRef = useRef(false)

  // Reaction-time tracking
  const reactionSamplesRef = useRef([])
  const appearanceSequenceRef = useRef(0)
  const recordedAppearancesRef = useRef(new Set())

  const [playerX, setPlayerX] = useState(375)
  const [playerY, setPlayerY] = useState(275)
  const [bullets, setBullets] = useState([])
  const [enemies, setEnemies] = useState([])

  const [score, setScore] = useState(0)
  const [health, setHealth] = useState(3)
  const [time, setTime] = useState(60)
  const [difficulty, setDifficulty] = useState('Medium')

  const [bulletsFired, setBulletsFired] = useState(0)
  const [enemiesDefeated, setEnemiesDefeated] = useState(0)
  const [playerHits, setPlayerHits] = useState(0)

  const [gameStarted, setGameStarted] = useState(false)
  const [explosions, setExplosions] = useState([])
  const [gameRunId, setGameRunId] = useState(0)

  // Live game values used by timers.
  const playerRef = useRef({ x: 375, y: 275 })
  const bulletsRef = useRef([])
  const enemiesRef = useRef([])
  const scoreRef = useRef(0)
  const healthRef = useRef(3)
  const timeRef = useRef(60)
  const bulletsFiredRef = useRef(0)
  const enemiesDefeatedRef = useRef(0)
  const playerHitsRef = useRef(0)
  const gameStartedRef = useRef(false)
  const difficultyRef = useRef('Medium')

  const gameOver = gameStarted && (health === 0 || time === 0)

  const difficultySpeeds = {
    Easy: [1, 1.5, 2],
    Medium: [2, 3, 4],
    Hard: [3, 4, 5]
  }

  const createEnemyAppearance = (enemy, speed = enemy.speed) => {
    appearanceSequenceRef.current += 1

    return {
      ...enemy,
      speed,
      visibleAt: performance.now(),
      appearanceId: appearanceSequenceRef.current
    }
  }

  const isColliding = (bullet, enemy) => (
    bullet.x < enemy.x + 40 &&
    bullet.x + 5 > enemy.x &&
    bullet.y < enemy.y + 40 &&
    bullet.y + 15 > enemy.y
  )

  const isPlayerHit = (currentPlayerX, currentPlayerY, enemy) => (
    currentPlayerX < enemy.x + 40 &&
    currentPlayerX + 40 > enemy.x &&
    currentPlayerY < enemy.y + 40 &&
    currentPlayerY + 40 > enemy.y
  )

  const changeDifficulty = (level) => {
    difficultyRef.current = level
    setDifficulty(level)

    const speeds = difficultySpeeds[level]
    const updatedEnemies = enemiesRef.current.map((enemy, index) => ({
      ...enemy,
      speed: speeds[index] ?? speeds[0]
    }))

    enemiesRef.current = updatedEnemies
    setEnemies(updatedEnemies)
  }

  // START / RESTART GAME
  const startGame = () => {
    dataSentRef.current = false
    reactionSamplesRef.current = []
    recordedAppearancesRef.current.clear()
    appearanceSequenceRef.current = 0

    const speeds = difficultySpeeds[difficultyRef.current]

    const initialEnemies = [
      createEnemyAppearance({ id: 1, x: 100, y: 50 }, speeds[0]),
      createEnemyAppearance({ id: 2, x: 380, y: 100 }, speeds[1]),
      createEnemyAppearance({ id: 3, x: 650, y: 50 }, speeds[2])
    ]

    playerRef.current = { x: 375, y: 275 }
    bulletsRef.current = []
    enemiesRef.current = initialEnemies
    scoreRef.current = 0
    healthRef.current = 3
    timeRef.current = 60
    bulletsFiredRef.current = 0
    enemiesDefeatedRef.current = 0
    playerHitsRef.current = 0
    gameStartedRef.current = true

    setPlayerX(375)
    setPlayerY(275)
    setBullets([])
    setEnemies(initialEnemies)
    setScore(0)
    setHealth(3)
    setTime(60)
    setBulletsFired(0)
    setEnemiesDefeated(0)
    setPlayerHits(0)
    setExplosions([])
    setGameStarted(true)
    setGameRunId((id) => id + 1)
  }

  // PLAYER MOVEMENT AND SHOOTING
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (!gameStartedRef.current || healthRef.current <= 0 || timeRef.current <= 0) {
        return
      }

      if (
        ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(event.key)
      ) {
        event.preventDefault()
      }

      const player = playerRef.current

      if (event.key === 'ArrowLeft') {
        const nextX = Math.max(0, player.x - 10)
        playerRef.current = { ...player, x: nextX }
        setPlayerX(nextX)
      }

      if (event.key === 'ArrowRight') {
        const nextX = Math.min(760, player.x + 10)
        playerRef.current = { ...player, x: nextX }
        setPlayerX(nextX)
      }

      if (event.key === 'ArrowUp') {
        const nextY = Math.max(0, player.y - 10)
        playerRef.current = { ...player, y: nextY }
        setPlayerY(nextY)
      }

      if (event.key === 'ArrowDown') {
        const nextY = Math.min(560, player.y + 10)
        playerRef.current = { ...player, y: nextY }
        setPlayerY(nextY)
      }

      if (event.code === 'Space' && !event.repeat) {
        const shotTime = performance.now()
        const currentPlayer = playerRef.current
        const bulletX = currentPlayer.x + 17
        const bulletY = currentPlayer.y - 15

        const possibleTargets = enemiesRef.current
          .filter((enemy) => (
            bulletX < enemy.x + 40 &&
            bulletX + 5 > enemy.x &&
            enemy.y < bulletY &&
            enemy.visibleAt !== undefined &&
            enemy.appearanceId !== undefined
          ))
          .sort((a, b) => b.y - a.y)

        const target = possibleTargets[0] ?? null
        let reactionSeconds = null
        let targetAppearanceId = null

        if (target) {
          const measuredTime = (shotTime - target.visibleAt) / 1000

          if (Number.isFinite(measuredTime) && measuredTime > 0) {
            reactionSeconds = measuredTime
            targetAppearanceId = target.appearanceId
          }
        }

        const newBullet = {
          id: `${shotTime}-${Math.random()}`,
          x: bulletX,
          y: bulletY,
          targetAppearanceId,
          reactionSeconds
        }

        const updatedBullets = [...bulletsRef.current, newBullet]
        bulletsRef.current = updatedBullets
        setBullets(updatedBullets)

        bulletsFiredRef.current += 1
        setBulletsFired(bulletsFiredRef.current)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // STABLE GAME LOOP
  useEffect(() => {
    if (!gameStarted) return undefined

    let lastTick = performance.now()
    let enemyElapsed = 0
    let collisionElapsed = 0
    let countdownElapsed = 0

    const gameTimer = setInterval(() => {
      const now = performance.now()
      const delta = Math.min(now - lastTick, 100)
      lastTick = now

      if (
        !gameStartedRef.current ||
        healthRef.current <= 0 ||
        timeRef.current <= 0
      ) {
        return
      }

      enemyElapsed += delta
      collisionElapsed += delta
      countdownElapsed += delta

      const currentEnemies = [...enemiesRef.current]
      const nextBullets = []
      const usedEnemySlots = new Set()
      const newExplosions = []
      let newKills = 0

      bulletsRef.current.forEach((bullet) => {
        let hitIndex = -1

        for (let index = 0; index < currentEnemies.length; index += 1) {
          if (usedEnemySlots.has(index)) continue

          if (isColliding(bullet, currentEnemies[index])) {
            hitIndex = index
            break
          }
        }

        if (hitIndex !== -1) {
          const hitEnemy = currentEnemies[hitIndex]

          const isIntendedTarget =
            bullet.targetAppearanceId !== null &&
            bullet.targetAppearanceId !== undefined &&
            bullet.targetAppearanceId === hitEnemy.appearanceId

          if (
            isIntendedTarget &&
            bullet.reactionSeconds !== null &&
            Number.isFinite(bullet.reactionSeconds) &&
            bullet.reactionSeconds > 0 &&
            !recordedAppearancesRef.current.has(hitEnemy.appearanceId)
          ) {
            reactionSamplesRef.current.push(bullet.reactionSeconds)
            recordedAppearancesRef.current.add(hitEnemy.appearanceId)

            console.log(
              'CONFIRMED REACTION TIME:',
              bullet.reactionSeconds.toFixed(3),
              'seconds'
            )
          }

          usedEnemySlots.add(hitIndex)
          newKills += 1

          newExplosions.push({
            id: `${now}-${Math.random()}`,
            x: hitEnemy.x,
            y: hitEnemy.y
          })

          currentEnemies[hitIndex] = createEnemyAppearance(
            {
              ...hitEnemy,
              x: Math.floor(Math.random() * 760),
              y: 50
            },
            hitEnemy.speed
          )
        } else if (bullet.y > -15) {
          nextBullets.push({ ...bullet, y: bullet.y - 10 })
        }
      })

      bulletsRef.current = nextBullets
      setBullets(nextBullets)

      if (newKills > 0) {
        enemiesRef.current = currentEnemies
        setEnemies(currentEnemies)

        scoreRef.current += newKills
        enemiesDefeatedRef.current += newKills
        setScore(scoreRef.current)
        setEnemiesDefeated(enemiesDefeatedRef.current)
      }

      if (newExplosions.length > 0) {
        setExplosions((oldExplosions) => [...oldExplosions, ...newExplosions])

        newExplosions.forEach((explosion) => {
          window.setTimeout(() => {
            setExplosions((oldExplosions) =>
              oldExplosions.filter((item) => item.id !== explosion.id)
            )
          }, 350)
        })
      }

      if (enemyElapsed >= 100) {
        const steps = Math.floor(enemyElapsed / 100)
        enemyElapsed %= 100

        const movedEnemies = enemiesRef.current.map((enemy) => {
          const nextY = enemy.y + enemy.speed * steps

          if (nextY >= 500) {
            return createEnemyAppearance(
              { ...enemy, x: enemy.x, y: 50 },
              enemy.speed
            )
          }

          return { ...enemy, y: nextY }
        })

        enemiesRef.current = movedEnemies
        setEnemies(movedEnemies)
      }

      if (collisionElapsed >= 500) {
        collisionElapsed %= 500
        const player = playerRef.current
        let damageCount = 0

        const updatedEnemies = enemiesRef.current.map((enemy) => {
          if (isPlayerHit(player.x, player.y, enemy)) {
            damageCount += 1

            return createEnemyAppearance(
              {
                ...enemy,
                x: Math.floor(Math.random() * 760),
                y: 50
              },
              enemy.speed
            )
          }

          return enemy
        })

        if (damageCount > 0) {
          enemiesRef.current = updatedEnemies
          setEnemies(updatedEnemies)

          healthRef.current = Math.max(0, healthRef.current - damageCount)
          playerHitsRef.current += damageCount
          setHealth(healthRef.current)
          setPlayerHits(playerHitsRef.current)
        }
      }

      if (countdownElapsed >= 1000) {
        const secondsToSubtract = Math.floor(countdownElapsed / 1000)
        countdownElapsed %= 1000

        timeRef.current = Math.max(0, timeRef.current - secondsToSubtract)
        setTime(timeRef.current)
      }
    }, 30)

    return () => clearInterval(gameTimer)
  }, [gameStarted, gameRunId])

  // SEND COMPLETED GAME DATA TO FLASK
  useEffect(() => {
    if (!gameOver || dataSentRef.current) return

    dataSentRef.current = true

    const finalScore = scoreRef.current
    const finalKills = enemiesDefeatedRef.current
    const finalHits = playerHitsRef.current
    const finalBullets = bulletsFiredRef.current
    const finalTime = timeRef.current
    const finalDifficulty = difficultyRef.current

    const accuracy = finalBullets > 0
      ? Math.round((finalKills / finalBullets) * 100)
      : 0

    const samples = [...reactionSamplesRef.current]

    const reactionTime = samples.length > 0
      ? Number((
          samples.reduce((total, value) => total + value, 0) / samples.length
        ).toFixed(3))
      : null

    const gameData = {
      score: finalScore,
      accuracy,
      kills: finalKills,
      deaths: finalHits,
      reaction_time: reactionTime,
      reaction_times: samples,
      survival_time: 60 - finalTime,
      damage_received: finalHits,
      difficulty: finalDifficulty,
      skill_level: finalKills >= 10
        ? 'Advanced'
        : finalKills >= 5
          ? 'Intermediate'
          : 'Beginner'
    }

    console.log('FINAL GAME DATA')
    console.table(gameData)
    console.log('CONFIRMED REACTION SAMPLES:', samples.length, samples)

    fetch(`${window.location.origin}/api/session`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(gameData)
    })
      .then(async (response) => {
        let data = {}

        try {
          data = await response.json()
        } catch (error) {
          throw new Error('Invalid response from Flask server')
        }

        if (!response.ok) {
          throw new Error(
            data.error ||
            data.message ||
            `Server returned HTTP ${response.status}`
          )
        }

        return data
      })
      .then((data) => {
        console.log('GAME DATA SAVED SUCCESSFULLY')
        console.log('SAVED REACTION TIME:', reactionTime)
        console.log('SAVED GAME SESSION:', data)
      })
      .catch((error) => {
        console.error('FAILED TO SEND GAME DATA')
        console.error(error)

        dataSentRef.current = false
      })
  }, [gameOver])

  const restartGame = () => {
    startGame()
  }

  const accuracy = bulletsFired > 0
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
                className={
                  difficulty === 'Easy' ? 'active easy' : 'easy'
                }
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
                className={
                  difficulty === 'Hard' ? 'active hard' : 'hard'
                }
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
              <span className="mission-tag">
                OPERATION: SURVIVAL
              </span>
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
              <span className="mission-objective">
                OBJECTIVE
              </span>
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
            className={
              difficulty === 'Easy' ? 'active easy' : 'easy'
            }
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
            className={
              difficulty === 'Hard' ? 'active hard' : 'hard'
            }
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

          {bullets.map((bullet) => (
            <div
              key={bullet.id}
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
              key={enemy.id}
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
                      background:
                        'linear-gradient(135deg, #1677ff, #9b5cff)',
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
