import { useState, useEffect } from 'react';

const useTheme = () => {
    const [theme, setTheme] = useState(
        () => localStorage.getItem('theme') || 'dark'
    )

    useEffect(() => {
        const root = window.documentElement
        if (theme === 'light') {
            root.classList.add('light')
        } else {
            root.classList.remove('light')
        }
        localStorage.setItem('theme', theme)
    }, [theme])

    const toggleTheme = ()  => {
        setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
    }

    return { theme, toggleTheme}
}

export default useTheme