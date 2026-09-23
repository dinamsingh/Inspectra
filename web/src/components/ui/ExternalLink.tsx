import type { AnchorHTMLAttributes } from 'react'

type ExternalLinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  href: string
}

export function ExternalLink({ href, children, ...props }: ExternalLinkProps) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
    </a>
  )
}
