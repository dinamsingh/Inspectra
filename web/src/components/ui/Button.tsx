import type { AnchorHTMLAttributes, ButtonHTMLAttributes } from 'react'
import styles from './Button.module.css'

type Variant = 'primary' | 'secondary'

type ButtonAsButton = ButtonHTMLAttributes<HTMLButtonElement> & {
  as?: 'button'
  variant?: Variant
}

type ButtonAsAnchor = AnchorHTMLAttributes<HTMLAnchorElement> & {
  as: 'a'
  variant?: Variant
}

type ButtonProps = ButtonAsButton | ButtonAsAnchor

export function Button({ variant = 'primary', className, ...props }: ButtonProps) {
  const classes = [styles.button, styles[variant], className].filter(Boolean).join(' ')

  if (props.as === 'a') {
    const { as: _as, ...anchorProps } = props
    return <a className={classes} {...anchorProps} />
  }

  const { as: _as, ...buttonProps } = props as ButtonAsButton
  return <button type="button" className={classes} {...buttonProps} />
}
