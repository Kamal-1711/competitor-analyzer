import { forwardRef, ButtonHTMLAttributes, ReactNode } from 'react'
import clsx from 'clsx'
import { Loader2 } from 'lucide-react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success'
    size?: 'sm' | 'md' | 'lg'
    loading?: boolean
    icon?: ReactNode
    iconPosition?: 'left' | 'right'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(({
    variant = 'primary',
    size = 'md',
    loading = false,
    icon,
    iconPosition = 'left',
    className,
    children,
    disabled,
    ...props
}, ref) => {
    const variants = {
        primary: 'bg-gradient-mesh text-white hover:opacity-90',
        secondary: 'bg-white/10 text-white hover:bg-white/20 border border-white/10',
        ghost: 'text-white/70 hover:text-white hover:bg-white/10',
        danger: 'bg-accent-red/20 text-accent-red hover:bg-accent-red/30 border border-accent-red/20',
        success: 'bg-accent-green/20 text-accent-green hover:bg-accent-green/30 border border-accent-green/20'
    }

    const sizes = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2',
        lg: 'px-6 py-3 text-lg'
    }

    return (
        <button
            ref={ref}
            disabled={disabled || loading}
            className={clsx(
                'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all',
                variants[variant],
                sizes[size],
                (disabled || loading) && 'opacity-50 cursor-not-allowed',
                className
            )}
            {...props}
        >
            {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
            ) : icon && iconPosition === 'left' ? (
                icon
            ) : null}
            {children}
            {!loading && icon && iconPosition === 'right' && icon}
        </button>
    )
})

Button.displayName = 'Button'

// Icon-only button
interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    icon: ReactNode
    variant?: 'primary' | 'secondary' | 'ghost'
    size?: 'sm' | 'md' | 'lg'
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(({
    icon,
    variant = 'ghost',
    size = 'md',
    className,
    ...props
}, ref) => {
    const sizes = {
        sm: 'w-7 h-7',
        md: 'w-9 h-9',
        lg: 'w-11 h-11'
    }

    const variants = {
        primary: 'bg-gradient-mesh text-white hover:opacity-90',
        secondary: 'bg-white/10 text-white hover:bg-white/20',
        ghost: 'text-white/60 hover:text-white hover:bg-white/10'
    }

    return (
        <button
            ref={ref}
            className={clsx(
                'inline-flex items-center justify-center rounded-lg transition-all',
                variants[variant],
                sizes[size],
                className
            )}
            {...props}
        >
            {icon}
        </button>
    )
})

IconButton.displayName = 'IconButton'

// Button group
interface ButtonGroupProps {
    children: ReactNode
    className?: string
}

export function ButtonGroup({ children, className }: ButtonGroupProps) {
    return (
        <div className={clsx(
            'inline-flex rounded-lg overflow-hidden border border-white/10',
            '[&>button]:rounded-none [&>button]:border-r [&>button]:border-white/10 [&>button:last-child]:border-r-0',
            className
        )}>
            {children}
        </div>
    )
}
