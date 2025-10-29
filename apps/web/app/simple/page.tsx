'use client'

import { useState, useEffect } from 'react'

export default function SimpleTest() {
  const [count, setCount] = useState(0)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    console.log('SimpleTest useEffect triggered')
    setMounted(true)
    setCount(1)
  }, [])

  console.log('SimpleTest render - mounted:', mounted, 'count:', count)

  if (!mounted) {
    return <div>Not mounted</div>
  }

  return (
    <div>
      <h1>Simple Test</h1>
      <p>Count: {count}</p>
      <p>Mounted: {mounted ? 'Yes' : 'No'}</p>
    </div>
  )
}
