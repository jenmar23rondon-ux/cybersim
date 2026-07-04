# Weak SSH server — CyberSim lab target.
# Password auth enabled, trivial credentials, no lockout. Local lab use only.
FROM alpine:3.20

RUN apk add --no-cache openssh \
    && ssh-keygen -A \
    # Create a couple of accounts with intentionally weak passwords.
    && adduser -D labuser \
    && echo "labuser:password123" | chpasswd \
    && echo "root:toor" | chpasswd \
    # Allow root + password login (insecure on purpose).
    && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D", "-e"]
