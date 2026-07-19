// animated background bubbles that rise and fade out
const BUBBLES = [
    { size: 20, left: 5,  duration: 8,  delay: 0   },
    { size: 35, left: 15, duration: 12, delay: 2   },
    { size: 15, left: 25, duration: 7,  delay: 4   },
    { size: 50, left: 35, duration: 15, delay: 1   },
    { size: 25, left: 50, duration: 10, delay: 6   },
    { size: 40, left: 60, duration: 13, delay: 3   },
    { size: 18, left: 70, duration: 9,  delay: 5   },
    { size: 55, left: 80, duration: 16, delay: 0.5 },
    { size: 22, left: 90, duration: 11, delay: 7   },
    { size: 30, left: 45, duration: 14, delay: 2.5 },
]

export default function Bubbles() {
    return (
        <div className="bubbles">
            {BUBBLES.map((b, i) => (
                <div key={i} className="bubble" style={{
                    width: b.size,
                    height: b.size,
                    left: `${b.left}%`,
                    animationDuration: `${b.duration}s`,
                    animationDelay: `${b.delay}s`,
                }} />
            ))}
        </div>
    )
}
