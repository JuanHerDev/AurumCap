
// Format currency - $1,284.97
export const formatCurrency = (value, decimals = 2) => {
    if (value == null || value == undefined) return  '-'
    return new Intl.NumberFormat('en-Us', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(value)
}

// Format crypto price - up to 6 decimals, remove trailing zeros
export const formatCryptoPrice = (value) => {
    if (value === null || value === undefined) return '-'
    if (value >= 1000 ) return formatCurrency(value, 2)
    if (value >= 1) return formatCurrency(value, 4)
    return formatCurrency(value, 6)
}

// Format percentage - +5.46% or -2.57%
export const formatPercentage = (value, showSign = true) => {
    if (value === null || value === undefined) return '-'
    const sign = showSign && value > 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
}

// Format large numbers - $1.2M, $3.64B
export const formatCompact = (value) => {
    if (value === null || value === undefined) return '-'
    return new Intl.NumberFormat('en-Us', {
        style: 'currency',
        currency: 'USD',
        notation: 'compact',
        maximumFractionDigits: 2,
    }).format(value)
}

// Format volume - 1,245,840
export const formatVolume = (value) => {
    if (value === null || value === undefined) return '-'
    return new Intl.NumberFormat('en-US', {
        notation: 'compact'
    }).format(value)
}

// Format date - Jan 1, 2026
export const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDayString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
    })
}

// Format date short - Jan 1
export const formatDateShort = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
    })
}

// Returns CSS class based on positive/negative value
export const colorCase = (value) => {
    if (value === null || value === undefined) return ''
    return value >= 0 ? 'positive' : 'negative'
}

// Returns + or - prefix symbol
export const signPrefix = (value)  => {
    if (value === null || value === undefined) return ''
    return value >= 0 ? '+' : ''
}